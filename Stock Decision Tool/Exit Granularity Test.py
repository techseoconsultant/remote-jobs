import os, json, urllib.request, urllib.parse, time, statistics as st, math, csv, collections
K=os.environ['ALPACA_API_KEY']; S=os.environ['ALPACA_SECRET_KEY']
H={"APCA-API-KEY-ID":K,"APCA-API-SECRET-KEY":S}
def get(url):
    req=urllib.request.Request(url,headers=H); return json.load(urllib.request.urlopen(req,timeout=120))
five={tuple(k.split("|")):v for k,v in json.load(open("movers_5m.json")).items()}
bydays=collections.defaultdict(list)
for (d,s) in five: bydays[d].append(s)
one={}; t0=time.time()
for d,syms in sorted(bydays.items()):
    tok=None; got={}
    while True:
        q={"symbols":",".join(syms),"timeframe":"1Min","start":f"{d}T13:30:00Z","end":f"{d}T20:00:00Z","feed":"sip","limit":10000,"adjustment":"raw"}
        if tok: q["page_token"]=tok
        r=get("https://data.alpaca.markets/v2/stocks/bars?"+urllib.parse.urlencode(q))
        for s,bs in (r.get("bars") or {}).items(): got.setdefault(s,[]).extend(bs)
        tok=r.get("next_page_token")
        if not tok: break
    for s,bs in got.items():
        bs=[b for b in sorted(bs,key=lambda b:b["t"]) if "13:30:00"<=b["t"][11:19]<"20:00:00"]
        if len(bs)>=300: one[(d,s)]=bs
print("1-min symbol-days",len(one),"bars",sum(len(v) for v in one.values()),"fetch s",round(time.time()-t0,1))

def vwap_series(bs):
    pv=vv=0; out=[]
    for b in bs:
        tp=(b["h"]+b["l"]+b["c"])/3; pv+=tp*b["v"]; vv+=b["v"]; out.append(pv/vv if vv else b["c"])
    return out
def atr_fn(bs, win):
    tr=[bs[0]["h"]-bs[0]["l"]]+[max(bs[i]["h"]-bs[i]["l"],abs(bs[i]["h"]-bs[i]["c"]),abs(bs[i]["l"]-bs[i]["c"])) for i in range(1,len(bs))]
    # note: use prev close properly
    tr=[bs[0]["h"]-bs[0]["l"]]+[max(bs[i]["h"]-bs[i]["l"],abs(bs[i]["h"]-bs[i-1]["c"]),abs(bs[i]["l"]-bs[i-1]["c"])) for i in range(1,len(bs))]
    return lambda i: sum(tr[max(0,i-win+1):i+1])/len(tr[max(0,i-win+1):i+1])

def test(gran, mult, cost):
    """Entry: at 10:00 ET if price>open and >VWAP (decided on the 5-min bars for comparability).
       Exit: trailing stop on `gran`-minute closes: close < highest close since entry - mult*ATR(60 min window)."""
    rets=[]; byday=collections.defaultdict(float); flips=[]
    for (d,s),b5 in five.items():
        bs = b5 if gran==5 else one.get((d,s))
        if bs is None: continue
        i10_5=next((i for i,b in enumerate(b5) if b["t"][11:16]>="14:00"),None)
        if i10_5 is None or i10_5+1>=len(b5): continue
        v5=vwap_series(b5)
        if not (b5[i10_5]["c"]>b5[0]["o"] and b5[i10_5]["c"]>v5[i10_5]): continue
        entry_t=b5[i10_5+1]["t"]  # fill at next 5-min bar open == the 1-min bar at same time
        ei=next((i for i,b in enumerate(bs) if b["t"]>=entry_t),None)
        if ei is None or ei>=len(bs)-1: continue
        ep=bs[ei]["o"]; win=12 if gran==5 else 60; atr=atr_fn(bs,win)
        hi=bs[ei]["c"]; xp=None
        for j in range(ei,len(bs)):
            hi=max(hi,bs[j]["c"])
            if j==len(bs)-1: xp=bs[j]["c"]; break
            if bs[j]["c"]<hi-mult*atr(j):
                xp=bs[j+1]["o"]; break
        r=(xp/ep-1)-2*cost; rets.append(r); byday[d]+=r
    mean=st.mean(rets); se=st.pstdev(rets)/math.sqrt(len(rets))
    return dict(granularity_min=gran,atr_mult=mult,cost_bps_per_side=int(cost*1e4),trades=len(rets),win_rate=round(sum(1 for r in rets if r>0)/len(rets),3),mean_ret_bps=round(mean*1e4,1),median_ret_bps=round(st.median(rets)*1e4,1),ci90_low_bps=round((mean-1.645*se)*1e4,1),ci90_high_bps=round((mean+1.645*se)*1e4,1),positive_days=f"{sum(1 for d in byday if byday[d]>0)}/{len(byday)}")
rows=[]
for gran in (5,1):
    for mult in (1.0,1.5,2.5):
        for cost in (0.0,0.0005,0.0010):
            rows.append(test(gran,mult,cost))
with open("/home/user/remote-jobs/Stock Decision Tool/Exit Granularity Test.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
for r in rows: print(r)
# how small are 1-minute and 1-second-scale moves on these movers? mean |1-min move| in bps
mv=[abs(bs[i]["c"]/bs[i-1]["c"]-1)*1e4 for bs in one.values() for i in range(1,len(bs)) if bs[i-1]["c"]>0]
print("movers mean |1-min move| bps",round(st.mean(mv),1),"median",round(st.median(mv),1))
