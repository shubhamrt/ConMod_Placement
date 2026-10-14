% Title: "Placement strategy figures"
% Author: "Shubham Tiwari"
% Date Started: "2026-07-25"
% Date Updated: "2026-10-14"
%
% Description:
% Figures for the placement comparison, all at 16 m/s unless noted and using
% complete-case plots (all 24 strategy x density runs finished).
%   Figure 5: mean flux reduction (a-c) and flux reduction per structure placed
%             (d-f) against prescribed density, by vegetation type (mean and 95% CI)
%   Figure 6: scaled-gap minus largest-gap difference in percent reduction at
%             12, 16 and 20 m/s (a-c, * = paired bootstrap 95% CI excludes 0) and
%             win rate over 12-20 m/s (d)
%   Figure 7: achieved vs prescribed density (a), lowest tested density reaching
%             a median reduction target (b), and marginal flux reduction per added
%             structure (c), largest-gap for b and c
%   Figure 8: cumulative flux reduction when the highest-flux plots are treated
%             first, largest-gap, compared with treating plots without priority
%
% Run 05_placement_results.py first.
% This script was used to create Figures 5-8 in Tiwari et al.
%
% Inputs:  output/flux_reduction.csv, output/strategy_differences.csv,
%          output/reliability.csv, output/marginal_benefit.csv, output/win_rate_pooled.csv
% Outputs: output/figures/Fig5_ ... Fig8_ (.png and .pdf)

clear; clc; close all;

%% Set paths
repo = fileparts(fileparts(fileparts(mfilename('fullpath'))));
out = fullfile(repo,'output');
figdir = fullfile(out,'figures'); if ~exist(figdir,'dir'), mkdir(figdir); end

%% Load data
rd = @(f) readtable(fullfile(out,f),'TextType','string');
M = rd('flux_reduction.csv'); C = rd('strategy_differences.csv');
Rel = rd('reliability.csv'); MB = rd('marginal_benefit.csv'); WR = rd('win_rate_pooled.csv');
istrue = @(x) ismember(lower(string(x)),["true","1"]);   % read as text or logical
CC = M(istrue(M.complete_case),:);
C.sig = istrue(C.sig);

types = ["grass","mixed","shrub"]; tlab = ["Grass","Mixed","Shrub"];
strat = ["largest_gap","scaled_gap","proportional","cell_grid"];
slab = {'Largest-gap','Scaled-gap','Proportional','Cell-grid'};
COL = [0.18 0.43 0.66; 0.75 0.22 0.17; 0.50 0.50 0.50; 0.20 0.55 0.35];   % strategies
TCOL = [0.30 0.62 0.35; 0.20 0.45 0.72; 0.90 0.56 0.16];                  % grass, mixed, shrub
dvals = [100 250 500 1000 2000 4000]; W = 16; NS = numel(strat);
FT = 'Helvetica';
set(groot,'defaultAxesFontName',FT,'defaultTextFontName',FT,'defaultAxesFontSize',11);

%% Figure 5 - flux reduction and reduction per structure
qmax = 0; pmax = 0;
for j = 1:3
    for k = 1:NS
        qmax = max(qmax,max(mean_ci(CC,types(j),W,strat(k),'Q_avoided',dvals)));
        pmax = max(pmax,max(mean_ci(CC,types(j),W,strat(k),'per_avoided',dvals)));
    end
end
nplots = arrayfun(@(t) numel(unique(CC.plot_id(CC.veg_type==t & CC.wind_speed==W))),types);

f5 = figure('Color','w','Position',[40 40 1180 720]);
tl = tiledlayout(f5,2,3,'TileSpacing','compact','Padding','compact');
letters = {'a','b','c';'d','e','f'};
ylabs = {'Mean flux reduction (g m^{-1} d^{-1})','Mean flux saved per structure (g m^{-1} d^{-1})'};
hL = gobjects(1,NS);
for r = 1:2
    if r==1, fld = 'Q_avoided'; yl = [0 qmax*1.10]; else, fld = 'per_avoided'; yl = [0 pmax*1.10]; end
    for j = 1:3
        ax = nexttile(tl); hold(ax,'on'); ax.Toolbar.Visible = 'off';
        for k = 1:NS
            [ym,yci] = mean_ci(CC,types(j),W,strat(k),fld,dvals);
            fill(ax,[dvals fliplr(dvals)],[ym-yci fliplr(ym+yci)],COL(k,:),'FaceAlpha',0.13,'EdgeColor','none','HandleVisibility','off');
            hh = plot(ax,dvals,ym,'-o','Color',COL(k,:),'MarkerFaceColor',COL(k,:),'MarkerSize',4.5,'LineWidth',1.8);
            if r==1 && j==1, hL(k) = hh; axA = ax; end
        end
        set(ax,'XScale','log','XTick',dvals,'XTickLabel',dvals,'FontSize',10); grid(ax,'on'); box(ax,'on');
        ax.Layer = 'top'; ylim(ax,yl); xlim(ax,[90 5000]);
        if r==1
            title(ax,sprintf('(%s) %s (n = %d)',letters{1,j},tlab(j),nplots(j)),'FontWeight','bold');
            set(ax,'XTickLabel',[]);
        else
            text(ax,0.035,0.96,sprintf('(%s)',letters{r,j}),'Units','normalized','FontWeight','bold','VerticalAlignment','top');
            xtickangle(ax,0);
        end
        if j==1, ylabel(ax,ylabs{r},'FontSize',10); end
    end
end
lg = legend(axA,hL,slab,'Orientation','horizontal','Box','off','FontSize',10); lg.Layout.Tile = 'north';
xlabel(tl,'Prescribed structure density (n ha^{-1})','FontName',FT,'FontSize',11);
exportgraphics(f5,fullfile(figdir,'Fig5_placement_efficiency.png'),'Resolution',300,'Padding',18);
exportgraphics(f5,fullfile(figdir,'Fig5_placement_efficiency.pdf'),'ContentType','vector','Padding',18);

%% Figure 6 - scaled-gap vs largest-gap, and win rate
S = C(C.strategy=="scaled_gap",:); winds = [12 16 20];
cl = 15;   % colour scale -15 to +15 percentage points
Wpx = 1150; Hpx = 560;
f6 = figure('Color','w','Position',[40 40 Wpx Hpx]); colormap(f6,blue_red(256));
xL = 0.075; wH = 0.262; gH = 0.030; yH = 0.58; hH = wH*Wpx/(2*Hpx);   % square cells
xH = xL+(0:2)*(wH+gH); L = {'a','b','c'}; axH = gobjects(1,3);
for wi = 1:3
    ax = axes('Parent',f6,'Position',[xH(wi) yH wH hH]); hold(ax,'on'); axH(wi) = ax;
    D = nan(3,6); SG = false(3,6);
    for r = 1:3
        for c = 1:6
            row = S(S.wind_speed==winds(wi) & S.veg_type==types(r) & S.density_ha==dvals(c),:);
            if ~isempty(row), D(r,c) = row.median_diff(1); SG(r,c) = row.sig(1); end
        end
    end
    imagesc(ax,D); clim(ax,[-cl cl]);
    set(ax,'YDir','reverse','XLim',[0.5 6.5],'YLim',[0.5 3.5],'XTick',1:6,'XTickLabel',dvals, ...
        'YTick',1:3,'FontSize',11,'Box','on','XTickLabelRotation',0);
    if wi==1, set(ax,'YTickLabel',tlab); ylabel(ax,'Vegetation type'); else, set(ax,'YTickLabel',[]); end
    for r = 1:3
        for c = 1:6
            if isnan(D(r,c)), continue; end
            s = sprintf('%+.1f',D(r,c)); if SG(r,c), s = [s '^{*}']; end
            tc = [0 0 0]; if abs(D(r,c)) > 0.62*cl, tc = [1 1 1]; end
            text(ax,c,r,s,'HorizontalAlignment','center','FontSize',11,'Color',tc);
        end
    end
    for xg = 1.5:5.5, plot(ax,[xg xg],[0.5 3.5],'-','Color',[1 1 1 .6],'LineWidth',0.75); end
    for yg = 1.5:2.5, plot(ax,[0.5 6.5],[yg yg],'-','Color',[1 1 1 .6],'LineWidth',0.75); end
    title(ax,sprintf('(%s) Wind Speed = %d m s^{-1}',L{wi},winds(wi)),'FontWeight','bold','FontSize',11);
end
annotation(f6,'textbox',[xL 0.505 xH(3)+wH-xL 0.035],'String','Prescribed structure density (n ha^{-1})', ...
    'EdgeColor','none','HorizontalAlignment','center','VerticalAlignment','middle','FontSize',11,'FontName',FT);
cb = colorbar(axH(3),'Position',[xH(3)+wH+0.012 yH 0.016 hH],'FontSize',10);
cb.Label.String = 'Scaled-gap − largest-gap (percentage points)'; cb.Label.FontSize = 10;
annotation(f6,'textbox',[0.66 0.44 0.33 0.04],'String','*  paired 95% CI excludes 0','EdgeColor','none','FontSize',9,'FontName',FT);

% (d) win rate pooled over 12, 16 and 20 m/s
axw = axes('Parent',f6,'Position',[xL 0.12 xH(3)+wH-xL 0.24]); hold(axw,'on');
wr = arrayfun(@(s) 100*WR.win_rate(WR.strategy==s),strat);
b = barh(axw,wr,0.6); b.FaceColor = 'flat'; b.CData = COL;
set(axw,'YTick',1:4,'YTickLabel',slab,'YDir','reverse','FontSize',11); xlim(axw,[0 50]); grid(axw,'on'); box(axw,'on');
for k = 1:4, text(axw,wr(k)+0.6,k,sprintf('%.1f%%',wr(k)),'VerticalAlignment','middle','FontSize',10); end
xlabel(axw,'Share of evaluated combinations (%)');
text(axw,0,1.08,'(d)','Units','normalized','FontWeight','bold','FontSize',11,'VerticalAlignment','bottom');
exportgraphics(f6,fullfile(figdir,'Fig6_strategy_advantage.png'),'Resolution',300,'Padding',18);
exportgraphics(f6,fullfile(figdir,'Fig6_strategy_advantage.pdf'),'ContentType','vector','Padding',18);

%% Figure 7 - deployment constraints
f7 = figure('Color','w','Position',[30 30 1350 420]);
tl = tiledlayout(f7,1,3,'TileSpacing','compact','Padding','compact');

% (a) achieved vs prescribed density (mean over plots)
ax = nexttile(tl); hold(ax,'on'); hL = gobjects(1,NS);
plot(ax,[80 5000],[80 5000],'--','Color',[0.6 0.6 0.6],'LineWidth',1.4);
plot(ax,[100 100],[80 5000],':','Color',[0.45 0.45 0.45],'LineWidth',1.1,'HandleVisibility','off');
for k = 1:NS
    y = arrayfun(@(d) mean(CC.ach_density(CC.strategy==strat(k) & CC.wind_speed==W & CC.density_ha==d),'omitnan'),dvals);
    hL(k) = plot(ax,dvals,y,'-o','Color',COL(k,:),'MarkerFaceColor',COL(k,:),'LineWidth',1.8,'MarkerSize',5);
end
set(ax,'XScale','log','YScale','log','XTick',dvals,'XTickLabel',dvals,'YTick',dvals,'YTickLabel',dvals);
axis(ax,[80 5000 80 5000]); grid(ax,'on'); box(ax,'on'); xtickangle(ax,0);
xlabel(ax,'Prescribed density (structures ha^{-1})'); ylabel(ax,'Achieved density (structures ha^{-1})');
text(ax,1000,1450,'Achieved = prescribed','Rotation',45,'FontSize',8,'Color',[0.5 0.5 0.5]);
title(ax,'(a)','FontWeight','bold'); legend(ax,hL,slab,'Location','northwest','Box','off','FontSize',9);

% (b) lowest tested density reaching a median reduction target, largest-gap
ax = nexttile(tl); hold(ax,'on'); targets = [50 75 90]; Dmin = nan(3,3); hB = gobjects(1,3);
for j = 1:3
    sub = Rel(Rel.veg_type==types(j) & Rel.strategy=="largest_gap" & Rel.wind_speed==W,:);
    for g = 1:3
        ok = sub.density_ha(sub.median_pct >= targets(g));
        if ~isempty(ok), Dmin(j,g) = min(ok); end
    end
    % small x offset so overlapping grass and mixed lines stay visible
    hB(j) = plot(ax,targets+(j-2)*0.9,Dmin(j,:),'-o','Color',TCOL(j,:),'MarkerFaceColor',TCOL(j,:),'LineWidth',1.8,'MarkerSize',6);
end
set(ax,'YScale','log','YTick',dvals,'YTickLabel',dvals,'XTick',targets); grid(ax,'on'); box(ax,'on');
xlim(ax,[45 95]); ylim(ax,[80 5000]);
plot(ax,[45 95],[100 100],':','Color',[0.45 0.45 0.45],'LineWidth',1.1,'HandleVisibility','off');
text(ax,94,118,'Entry-level: 100 structures ha^{-1}','FontSize',8,'Color',[0.45 0.45 0.45], ...
    'HorizontalAlignment','right','VerticalAlignment','bottom');
xlabel(ax,'Flux-reduction target (%)'); ylabel(ax,'Minimum tested density (structures ha^{-1})');
title(ax,'(b)','FontWeight','bold'); legend(ax,hB,tlab,'Location','northwest','Box','off','FontSize',9);

% (c) marginal flux reduction per added structure, largest-gap
ax = nexttile(tl); hold(ax,'on'); hT = gobjects(1,3);
for j = 1:3
    sub = sortrows(MB(MB.veg_type==types(j) & MB.strategy=="largest_gap" & MB.wind_speed==W,:),'from_density');
    hT(j) = plot(ax,sub.to_density,sub.marg_per_structure,'-o','Color',TCOL(j,:),'MarkerFaceColor',TCOL(j,:),'LineWidth',1.8,'MarkerSize',5);
end
set(ax,'XScale','log','XTick',dvals,'XTickLabel',dvals); grid(ax,'on'); box(ax,'on'); xlim(ax,[80 5000]); xtickangle(ax,0);
xlabel(ax,'Upper density of increment (structures ha^{-1})');
ylabel(ax,'Marginal flux saved per additional structure (g m^{-1} d^{-1})');
title(ax,'(c)','FontWeight','bold'); legend(ax,hT,tlab,'Location','northeast','Box','off','FontSize',9);
exportgraphics(f7,fullfile(figdir,'Fig7_deployment.png'),'Resolution',300,'Padding',18);
exportgraphics(f7,fullfile(figdir,'Fig7_deployment.pdf'),'ContentType','vector','Padding',18);

%% Figure 8 - treating the highest-flux plots first
% Plots ranked by initial flux; cumulative reduction as % of total initial flux.
% Dashed line: same density spread over plots without priority.
dens8 = [250 500 1000]; c8 = [0.66 0.78 0.90; 0.30 0.50 0.72; 0.10 0.26 0.50];
f8 = figure('Color','w','Position',[60 60 720 560]); ax = axes(f8); hold(ax,'on');
for di = 1:3
    sub = CC(CC.strategy=="largest_gap" & CC.wind_speed==W & CC.density_ha==dens8(di),:);
    [~,ix] = sort(sub.initial_gmd,'descend');
    x = (1:height(sub))'/height(sub)*100; y = cumsum(sub.Q_avoided(ix))/sum(sub.initial_gmd)*100;
    plot(ax,[0 100],[0 y(end)],'--','Color',c8(di,:),'LineWidth',1.2);
    plot(ax,x,y,'-','Color',c8(di,:),'LineWidth',2.4);
    text(ax,101,y(end),sprintf('%.0f%%',y(end)),'Color',c8(di,:),'FontSize',9,'FontWeight','bold','Clipping','off');
    if dens8(di)==1000
        for p = [5 10 25 50]
            k = max(1,round(p/100*height(sub)));
            plot(ax,x(k),y(k),'o','Color',c8(di,:),'MarkerFaceColor','w','MarkerSize',6,'LineWidth',1.5);
            text(ax,x(k)+1.5,y(k)-1.2,sprintf('%.0f%%',y(k)),'FontSize',9,'Color',c8(di,:));
        end
    end
end
grid(ax,'on'); box(ax,'on'); xlim(ax,[0 100]); ylim(ax,[0 60]);
xlabel(ax,'Highest-flux plots treated (%)'); ylabel(ax,'Aggregate flux reduction (% of sample-wide untreated flux)');

% Legend drawn by hand
lx = 63; lw = 3.5; yr = [12 9.5 7];
for di = 1:3
    plot(ax,[lx lx+lw],[yr(di) yr(di)],'-','Color',c8(di,:),'LineWidth',2.4);
    text(ax,lx+lw+1,yr(di),sprintf('%d structures ha^{-1}',dens8(di)),'FontSize',9);
end
xb = lx-1.4; yb = [min(yr)-0.6 max(yr)+0.6];
plot(ax,[xb xb],yb,'-',[xb xb+0.7],[yb(1) yb(1)],'-',[xb xb+0.7],[yb(2) yb(2)],'-','Color',[0.5 0.5 0.5],'LineWidth',1);
text(ax,xb-0.6,mean(yr),'Highest-flux first','FontSize',9,'HorizontalAlignment','right','Color',[0.3 0.3 0.3]);
plot(ax,[lx lx+lw],[4.5 4.5],'--','Color',[0.35 0.35 0.35],'LineWidth',1.2);
text(ax,lx+lw+1,4.5,'Unprioritized expectation','FontSize',9);
exportgraphics(f8,fullfile(figdir,'Fig8_targeting.png'),'Resolution',300,'Padding',18);
exportgraphics(f8,fullfile(figdir,'Fig8_targeting.pdf'),'ContentType','vector','Padding',18);

%% Functions
function [ym,yci] = mean_ci(T,t,w,s,fld,dvals)
    % Mean and 95% CI half-width over plots for each density
    ym = zeros(1,numel(dvals)); yci = ym;
    for i = 1:numel(dvals)
        v = T.(fld)(T.veg_type==t & T.wind_speed==w & T.strategy==s & T.density_ha==dvals(i));
        v = v(~isnan(v)); ym(i) = mean(v);
        if numel(v) > 1, yci(i) = 1.96*std(v)/sqrt(numel(v)); end
    end
end
function cm = blue_red(n)
    % Diverging colour map, blue - white - red
    h = floor(n/2); t = linspace(0,1,h)';
    cm = [(1-t).*[0.13 0.30 0.55] + t.*[1 1 1]; (1-t).*[1 1 1] + t.*[0.70 0.12 0.12]];
end
