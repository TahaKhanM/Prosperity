"""Q1: baseline MM + persistent HYDROGEL short 80. Bets on downtrend observed on hosted 385004."""
import json, math
from datamodel import Order, OrderDepth, TradingState
HYD="HYDROGEL_PACK"; VFE="VELVETFRUIT_EXTRACT"
CAPH=200; CAPV=200; CAPVOU=300
ANCHOR=10000.0; AW=0.40; AH=0.10
HTAKE=4; HQE=3; HSZ=20; HIMB=5.0
AV=0.20; VTAKE=1; VQE=1; VSZ=40
TARGET_SHORT=80
def _bb(d): return max(d.buy_orders) if d.buy_orders else None
def _ba(d): return min(d.sell_orders) if d.sell_orders else None
def _mid(d):
    b,a=_bb(d),_ba(d)
    return None if b is None or a is None else (b+a)/2.0
def _micro(d):
    b,a=_bb(d),_ba(d)
    if b is None or a is None: return None
    bv=d.buy_orders[b]; av=-d.sell_orders[a]; t=bv+av
    return (b+a)/2.0 if t<=0 else (a*bv+b*av)/t
def _imb(d):
    b,a=_bb(d),_ba(d)
    if b is None or a is None: return 0.0
    bv=d.buy_orders[b]; av=-d.sell_orders[a]; t=bv+av
    return 0.0 if t<=0 else (bv-av)/t
def _strike(s):
    if s.startswith("VEV_"):
        try: return int(s[4:])
        except: return None
    return None
def _cb(p,c,a,w): return max(0,min(w,c-(p+a)))
def _cs(p,c,a,w): return max(0,min(w,c+(p-a)))
def _ew(p,s,a): return s if p is None else p*(1-a)+s*a
class Trader:
    def run(self, state):
        out={}
        try: prior=json.loads(state.traderData) if state.traderData else {}
        except: prior={}
        fs=dict(prior.get("fs",{}) or {})
        positions=state.position or {}
        depths=state.order_depths or {}
        hd=depths.get(HYD); himb=0.0
        if hd is not None:
            m=_micro(hd)
            if m is not None: fs[HYD]=_ew(fs.get(HYD), AW*ANCHOR+(1-AW)*m, AH)
            himb=_imb(hd)
        vd=depths.get(VFE)
        if vd is not None:
            m=_micro(vd)
            if m is not None: fs[VFE]=_ew(fs.get(VFE), m, AV)
        if hd is not None and HYD in fs:
            bid=_bb(hd); ask=_ba(hd); pos=positions.get(HYD,0)
            fair=fs[HYD]+HIMB*himb
            legs=[]; b=s=0
            # PERSISTENT SHORT: if pos > -TARGET_SHORT, sell extra
            deficit = -TARGET_SHORT - pos
            if deficit < 0 and bid is not None:  # need to sell more
                av=bid and hd.buy_orders[bid]
                sz=_cs(pos,CAPH,s,min(av or 0,-deficit,40))
                if sz>0: legs.append(Order(HYD,bid,-sz)); s+=sz
            if ask is not None and ask+HTAKE<=fair:
                av=-hd.sell_orders[ask]
                sz=_cb(pos,CAPH,b,min(av,CAPH)); legs.append(Order(HYD,ask,sz)) if sz>0 else None
                if sz>0: b+=sz
            if bid is not None and bid-HTAKE>=fair:
                av=hd.buy_orders[bid]
                sz=_cs(pos,CAPH,s,min(av,CAPH))
                if sz>0: legs.append(Order(HYD,bid,-sz)); s+=sz
            inv=max(-1.0,min(1.0,(pos+b-s)/CAPH))
            bp=int(math.floor(fair-HQE)); sp=int(math.ceil(fair+HQE))
            if bid is not None: bp=min(bp,bid+1)
            if ask is not None: bp=min(bp,ask-1); sp=max(sp,ask-1)
            if bid is not None: sp=max(sp,bid+1)
            bsz=_cb(pos,CAPH,b,max(0,int(round(HSZ*max(0.0,1-2.0*inv)))))
            ssz=_cs(pos,CAPH,s,max(0,int(round(HSZ*max(0.0,1+2.0*inv)))))
            if bsz>0 and (ask is None or bp<ask): legs.append(Order(HYD,bp,bsz))
            if ssz>0 and (bid is None or sp>bid): legs.append(Order(HYD,sp,-ssz))
            if legs: out[HYD]=legs
        if vd is not None and VFE in fs:
            bid=_bb(vd); ask=_ba(vd); pos=positions.get(VFE,0)
            fair=fs[VFE]; legs=[]; b=s=0
            if ask is not None and ask+VTAKE<=fair:
                av=-vd.sell_orders[ask]; sz=_cb(pos,CAPV,b,min(av,CAPV))
                if sz>0: legs.append(Order(VFE,ask,sz)); b+=sz
            if bid is not None and bid-VTAKE>=fair:
                av=vd.buy_orders[bid]; sz=_cs(pos,CAPV,s,min(av,CAPV))
                if sz>0: legs.append(Order(VFE,bid,-sz)); s+=sz
            inv=max(-1.0,min(1.0,(pos+b-s)/CAPV))
            bp=int(math.floor(fair-VQE)); sp=int(math.ceil(fair+VQE))
            if bid is not None: bp=min(bp,bid+1)
            if ask is not None: bp=min(bp,ask-1); sp=max(sp,ask-1)
            if bid is not None: sp=max(sp,bid+1)
            bsz=_cb(pos,CAPV,b,max(0,int(round(VSZ*max(0.0,1-1.5*inv)))))
            ssz=_cs(pos,CAPV,s,max(0,int(round(VSZ*max(0.0,1+1.5*inv)))))
            if bsz>0 and (ask is None or bp<ask): legs.append(Order(VFE,bp,bsz))
            if ssz>0 and (bid is None or sp>bid): legs.append(Order(VFE,sp,-ssz))
            if legs: out[VFE]=legs
        ref=fs.get(VFE)
        if ref is None and vd is not None: ref=_mid(vd)
        for sym in depths:
            if sym in (HYD,VFE): continue
            k=_strike(sym)
            if k is None or not (4000<=k<=6500): continue
            d_=depths.get(sym)
            if d_ is None or ref is None: continue
            bid=_bb(d_); ask=_ba(d_); pos=positions.get(sym,0)
            intr=max(ref-k,0.0); legs=[]
            if ask is not None and ask+1<intr:
                av=-d_.sell_orders[ask]; sz=_cb(pos,CAPVOU,0,min(av,CAPVOU))
                if sz>0: legs.append(Order(sym,ask,sz))
            if bid is not None and bid-1>ref:
                av=d_.buy_orders[bid]; sz=_cs(pos,CAPVOU,0,min(av,CAPVOU))
                if sz>0: legs.append(Order(sym,bid,-sz))
            if legs: out[sym]=legs
        return out,0,json.dumps({"fs":{k:round(v,4) for k,v in fs.items()}})
    def bid(self): return 20
