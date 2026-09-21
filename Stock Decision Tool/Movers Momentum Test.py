import os, json, urllib.request, urllib.parse, time, statistics as st, math, csv, collections
K=os.environ['ALPACA_API_KEY']; S=os.environ['ALPACA_SECRET_KEY']
H={"APCA-API-KEY-ID":K,"APCA-API-SECRET-KEY":S}
def get(url, tries=3):
    for a in range(tries):
        try:
            req=urllib.request.Request(url,headers=H); return json.load(urllib.request.urlopen(req,timeout=120))
        except urllib.error.HTTPError as e:
            if e.code in (403,422): raise
            if a==tries-1: raise
            time.sleep(2)
        except Exception:
            if a==tries-1: raise
            time.sleep(2)
daily=json.load(open("daily_universe.json"))
for s in daily: daily[s].sort(key=lambda b:b["t"])
days=sorted({b["t"][:10] for b in daily["SPY"]})
test_days=[d for d in days if "2026-08-20"<=d<="2026-09-18"]
print("trading days in test",len(test_days))
# screen
cands=collections.defaultdict(dict)  # day -> symbol -> info
for s,bs in daily.items():
    idx={b["t"][:10]:i for i,b in enumerate(bs)}
    for d in test_days:
        i=idx.get(d)
        if i is None or i<21: continue
        prev=bs[i-1]; cur=bs[i]
        if not (5<=prev["c"]<=1250): continue
        adv=st.mean(b["c"]*b["v"] for b in bs[i-21:i-1])
        if adv<20e6: continue
        gap=cur["o"]/prev["c"]-1
        prevret=prev["c"]/bs[i-2]["c"]-1
        if gap>=0.03: cands[d][s]=dict(set="gap",gap=gap,prevret=prevret,adv=adv,dopen=cur["o"],pclose=prev["c"])
        elif prevret>=0.05: cands[d][s]=dict(set="prevmover",gap=gap,prevret=prevret,adv=adv,dopen=cur["o"],pclose=prev["c"])
# cap per day: top 30 gaps + top 30 prev movers
sel={}
for d in test_days:
    items=cands[d]
    g=sorted([(v["gap"],s) for s,v in items.items() if v["set"]=="gap"],reverse=True)[:30]
    p=sorted([(v["prevret"],s) for s,v in items.items() if v["set"]=="prevmover"],reverse=True)[:30]
    sel[d]={s:items[s] for _,s in g+p}
print("candidate symbol-days",sum(len(v) for v in sel.values()),"per day avg",round(st.mean(len(v) for v in sel.values()),1))
# intraday bars per day
feed_used=None; bars={}
t0=time.time()
for d in test_days:
    symsd=list(sel[d]); 
    if not symsd: continue
    for feed in (["sip","iex"] if feed_used is None else [feed_used]):
        try:
            tok=None; got={}
            while True:
                q={"symbols":",".join(symsd),"timeframe":"5Min","start":f"{d}T13:30:00Z","end":f"{d}T20:00:00Z","feed":feed,"limit":10000,"adjustment":"raw"}
                if tok: q["page_token"]=tok
                r=get("https://data.alpaca.markets/v2/stocks/bars?"+urllib.parse.urlencode(q))
                for s,bs in (r.get("bars") or {}).items(): got.setdefault(s,[]).extend(bs)
                tok=r.get("next_page_token")
                if not tok: break
            feed_used=feed; break
        except urllib.error.HTTPError as e:
            print("feed",feed,"HTTP",e.code); continue
    for s,bs in got.items():
        bs=[b for b in sorted(bs,key=lambda b:b["t"]) if "13:30:00"<=b["t"][11:19]<"20:00:00"]
        if len(bs)>=60: bars[(d,s)]=bs
print("intraday feed",feed_used,"symbol-days with >=60 bars",len(bars),"fetch s",round(time.time()-t0,1))
json.dump({f"{d}|{s}":v for (d,s),v in bars.items()},open("movers_5m.json","w"))

def run_rules(bars, cost_side):
    out=collections.defaultdict(list)   # rule -> list of (day, net_ret)
    c=cost_side
    for (d,s),bs in bars.items():
        o=[b["o"] for b in bs]; h=[b["h"] for b in bs]; l=[b["l"] for b in bs]; cl=[b["c"] for b in bs]; v=[b["v"] for b in bs]
        n=len(bs); dopen=o[0]
        # vwap
        cum_pv=0; cum_v=0; vwap=[]
        for i in range(n):
            tp=(h[i]+l[i]+cl[i])/3; cum_pv+=tp*v[i]; cum_v+=v[i]; vwap.append(cum_pv/cum_v if cum_v else cl[i])
        # ATR12
        tr=[h[0]-l[0]]+[max(h[i]-l[i],abs(h[i]-cl[i-1]),abs(l[i]-cl[i-1])) for i in range(1,n)]
        def atr(i): 
            w=tr[max(0,i-11):i+1]; return sum(w)/len(w)
        i10=next((i for i,b in enumerate(bs) if b["t"][11:16]>="14:00"),None)  # 10:00 ET
        if i10 is None or i10+1>=n: continue
        or_high=max(h[:6]) if n>=6 else h[0]
        last=n-1
        def trade(entry_i, exit_rule):
            # fill at next bar open
            if entry_i+1>=n: return None
            ep=o[entry_i+1]; hi=cl[entry_i+1]
            for j in range(entry_i+1,n):
                hi=max(hi,cl[j])
                if j==last: xp=cl[j]; break
                if exit_rule=="close": continue
                stop=hi-1.5*atr(j)
                if cl[j]<stop:
                    if j+1<n: xp=o[j+1]
                    else: xp=cl[j]
                    break
            else: xp=cl[last]
            return (xp/ep-1)-2*c
        # R0: hold from 10:00 to close, no condition (does the mover continue?)
        r=trade(i10,"close"); 
        if r is not None: out["R0 hold 10:00 to close, all movers"].append((d,r))
        # R1: buy strength at 10:00 (above open and VWAP), hold to close
        if cl[i10]>dopen and cl[i10]>vwap[i10]:
            r=trade(i10,"close"); 
            if r is not None: out["R1 buy strength 10:00, sell at close"].append((d,r))
            r=trade(i10,"trail"); 
            if r is not None: out["R2 buy strength 10:00, trailing stop 1.5 ATR"].append((d,r))
        # R3: opening range breakout after 10:00 with VWAP filter
        for i in range(i10,n-1):
            if cl[i]>or_high and cl[i]>vwap[i]:
                r=trade(i,"trail"); 
                if r is not None: out["R3 opening range breakout, trailing stop"].append((d,r))
                break
        # R4: literal momentum flip: buy when close>close[-3], sell when close<close[-3], repeat, from 10:00
        pos=None; total=0.0; ntr=0
        for i in range(i10,n-1):
            if pos is None and cl[i]>cl[i-3]:
                pos=o[i+1]
            elif pos is not None and cl[i]<cl[i-3]:
                total+=(o[i+1]/pos-1)-2*c; ntr+=1; pos=None
        if pos is not None: total+=(cl[last]/pos-1)-2*c; ntr+=1
        if ntr: out["R4 buy on 3-bar up, sell on 3-bar down, all day"].append((d,total)); out["_R4_trades_per_symbolday"].append((d,ntr))
    return out

rows=[]
for c in (0.0,0.0005,0.0010,0.0020):
    res=run_rules(bars,c)
    for rule,lst in res.items():
        if rule.startswith("_"): continue
        rets=[r for _,r in lst]
        byday=collections.defaultdict(float)
        for d,r in lst: byday[d]+=r
        pos_days=sum(1 for d in byday if byday[d]>0)
        mean=st.mean(rets); med=st.median(rets); win=sum(1 for r in rets if r>0)/len(rets)
        se=st.pstdev(rets)/math.sqrt(len(rets))
        rows.append(dict(cost_bps_per_side=int(c*1e4),rule=rule,trades=len(rets),win_rate=round(win,3),mean_ret_bps=round(mean*1e4,1),median_ret_bps=round(med*1e4,1),ci90_mean_low_bps=round((mean-1.645*se)*1e4,1),ci90_mean_high_bps=round((mean+1.645*se)*1e4,1),positive_days=f"{pos_days}/{len(byday)}",sum_all_trades_pct=round(sum(rets)*100,1)))
r4=[n for _,n in run_rules(bars,0)["_R4_trades_per_symbolday"]]
print("R4 round trips per symbol-day: mean",round(st.mean(r4),1),"median",st.median(r4))
with open("/home/user/remote-jobs/Stock Decision Tool/Movers Momentum Baselines.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
for r in rows: print(r)
# how did the movers themselves do 10:00->close on average, split by set
cont=collections.defaultdict(list)
for (d,s),bs in bars.items():
    i10=next((i for i,b in enumerate(bs) if b["t"][11:16]>="14:00"),None)
    if i10 is None: continue
    cont[sel[d][s]["set"]].append(bs[-1]["c"]/bs[i10]["o"]-1)
for k,v in cont.items(): print("continuation 10:00->close",k,"n",len(v),"mean bps",round(st.mean(v)*1e4,1),"median bps",round(st.median(v)*1e4,1),"share positive",round(sum(1 for x in v if x>0)/len(v),3))
