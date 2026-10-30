"""Small multiples of rolling top-flight G, seven leagues. Usage: python -I trend_xc_figure.py rolling_G_topflight.csv out.png"""
import sys, pandas as pd, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
SURF='#fcfcfb'; INK='#0b0b0b'; INK2='#52514e'; GRID='#e4e3df'; S1='#2a78d6'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.edgecolor':GRID,'xtick.color':INK2,'ytick.color':INK2,'text.color':INK})
R=pd.read_csv(sys.argv[1]); R=R[np.isfinite(R.G)&(R.G>0)]
names={'ENG':'England','ESP':'Spain','ITA':'Italy','GER':'Germany','FRA':'France','NED':'Netherlands','POR':'Portugal'}
order=['ENG','ESP','ITA','GER','FRA','NED','POR']
fig,axs=plt.subplots(2,4,figsize=(10,5.2),dpi=200,sharex=True,sharey=True); fig.patch.set_facecolor(SURF)
for ax,c in zip(axs.flat,order):
    d=R[R.country==c].sort_values('mid'); ax.set_facecolor(SURF)
    ax.plot(d.mid,d.G.clip(upper=8),color=S1,lw=2)
    if (d.G>8).any(): ax.text(d.mid.max(),7.6,'off scale →',ha='right',fontsize=7,color=INK2)
    ax.axvline(1992.5,color=INK2,lw=0.8,ls=(0,(3,3)))
    ax.set_title(names[c],loc='left',fontsize=9.5,fontweight='bold')
    for s in ('top','right'): ax.spines[s].set_visible(False)
    ax.grid(axis='y',color=GRID,lw=0.7); ax.set_axisbelow(True); ax.set_ylim(0,8); ax.set_xlim(1962,2020)
axs.flat[-1].axis('off')
axs.flat[-1].text(0.02,0.75,'Top flight only:\nlevels are biased by\ntruncation, trends are not\n(England: r = 0.99 with its\nfour-tier series).\n\nDashed line: 1992.\nHigher G = less mobile.',fontsize=8,color=INK2,va='top',transform=axs.flat[-1].transAxes)
fig.suptitle("England's collapse came first; Spain's followed more than a decade later",x=0.06,ha='left',fontsize=11.5,fontweight='bold')
fig.text(0.06,0.905,'Rolling 12-season G, top flight, x = window midpoint. Source: engsoccerdata, cleaned and gap-patched; repaired seasons checked against published tables (D239).',fontsize=8,color=INK2)
fig.tight_layout(rect=(0,0,1,0.9)); fig.savefig(sys.argv[2],facecolor=SURF); print('ok')
