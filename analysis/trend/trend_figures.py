"""Figures for Long_Run_Mobility_Trend_England.md. Usage: python -I trend_figures.py <eng_rolling_G.csv> <outdir>"""
import sys, pandas as pd, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
SURF='#fcfcfb'; INK='#0b0b0b'; INK2='#52514e'; GRID='#e4e3df'; S1='#2a78d6'; S2='#eb6834'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.edgecolor':GRID,'axes.labelcolor':INK2,'xtick.color':INK2,'ytick.color':INK2,'text.color':INK})
R=pd.read_csv(sys.argv[1]); out=sys.argv[2]
# Figure 1: rolling G, England four tiers
fig,ax=plt.subplots(figsize=(8.6,4.4),dpi=200); fig.patch.set_facecolor(SURF); ax.set_facecolor(SURF)
ax.fill_between(R['mid'],R['lo'],R['hi'],color=S1,alpha=0.14,linewidth=0)
ax.plot(R['mid'],R['G'],color=S1,lw=2,solid_capstyle='round')
ax.axvline(1992.5,color=INK2,lw=1,ls=(0,(3,3)))
ax.text(1993.2,8.6,'Premier League\nbegins 1992/93',color=INK2,fontsize=8.5,va='top')
pk=R.loc[R.G.idxmax()]
ax.plot([pk.mid],[pk.G],'o',ms=7,color=S1,markeredgecolor=SURF,markeredgewidth=2)
ax.annotate(f"peak {pk.G:.1f}\n({pk.window})",(pk.mid,pk.G),xytext=(pk.mid+2.2,pk.G+0.9),fontsize=8.5,color=INK)
first=R.iloc[0]; last=R.iloc[-1]
ax.annotate(f"{first.G:.1f}",(first.mid,first.G),xytext=(first.mid-0.4,first.G+0.55),fontsize=8.5,color=INK)
ax.annotate(f"{last.G:.1f}",(last.mid,last.G),xytext=(last.mid+0.6,last.G-0.1),fontsize=8.5,color=INK)
for s in ('top','right'): ax.spines[s].set_visible(False)
ax.grid(axis='y',color=GRID,lw=0.8); ax.set_axisbelow(True)
ax.set_xlim(1963,2021); ax.set_ylim(0,13)
ax.set_xlabel('Midpoint of 12-season window'); ax.set_ylabel('G  (observed ÷ chance-level)')
fig.suptitle('English competitive mobility collapsed in the 1990s and has only partly recovered',x=0.065,ha='left',fontsize=11.5,fontweight='bold')
ax.set_title('Seasons from the bottom half of the top flight to its top four, relative to chance.\nFour-tier pyramid, rolling 12-season windows, 1958–2024. Shaded: 95% bootstrap interval.',loc='left',fontsize=8.3,color=INK2)
fig.text(0.065,0.01,'Higher G = less mobile. Source: engsoccerdata; 2022/23 from openfootball. Football Research project, 8 Oct 2026.',fontsize=7,color=INK2)
fig.tight_layout(rect=(0,0.03,1,0.97)); fig.savefig(f'{out}/fig1_england_rolling_G.png',facecolor=SURF); plt.close(fig)
# Figure 2: England vs Germany, two tiers, eras
eras=['1981–92','1992–2003','2003–14','2014–24']; xs=[1986.5,1997.5,2008.5,2019]
eng=[(2.16,1.81,2.50),(3.59,2.76,4.90),(5.79,4.67,8.93),(3.32,2.56,5.06)]
ger=[(2.64,2.11,3.47),(2.08,1.69,2.56),(2.80,2.26,3.83),(3.04,2.29,3.84)]
fig,ax=plt.subplots(figsize=(8.6,4.2),dpi=200); fig.patch.set_facecolor(SURF); ax.set_facecolor(SURF)
for data,col,lab,off in [(eng,S1,'England',-0.5),(ger,S2,'Germany',0.5)]:
    x=[v+off for v in xs]; g=[d[0] for d in data]
    ax.vlines(x,[d[1] for d in data],[d[2] for d in data],color=col,lw=2,alpha=0.35)
    ax.plot(x,g,color=col,lw=2); ax.plot(x,g,'o',ms=8,color=col,markeredgecolor=SURF,markeredgewidth=2,label=lab)
    ax.annotate(lab,(x[-1],g[-1]),xytext=(x[-1]+1.4,g[-1]+(0.25 if lab=='England' else -0.35)),fontsize=9,color=INK,fontweight='bold')
for s in ('top','right'): ax.spines[s].set_visible(False)
ax.grid(axis='y',color=GRID,lw=0.8); ax.set_axisbelow(True)
ax.set_xticks(xs); ax.set_xticklabels(eras); ax.set_xlim(1982,2025); ax.set_ylim(0,9.5)
ax.set_ylabel('G  (observed ÷ chance-level)')
ax.legend(frameon=False,loc='upper left',fontsize=9)
fig.suptitle('Germany, exposed to the same European changes, shows no comparable break',x=0.065,ha='left',fontsize=11.5,fontweight='bold')
ax.set_title('Two-tier pyramid in both countries, non-overlapping eras. Lines: 95% bootstrap intervals.',loc='left',fontsize=8.3,color=INK2)
fig.text(0.065,0.01,'Higher G = less mobile. A comparison, not a control: no causal claim is made (D193). Source: engsoccerdata.',fontsize=7,color=INK2)
fig.tight_layout(rect=(0,0.03,1,0.97)); fig.savefig(f'{out}/fig2_england_germany_eras.png',facecolor=SURF); plt.close(fig)
print('ok')
