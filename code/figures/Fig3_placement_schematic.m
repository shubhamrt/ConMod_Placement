% Title: "Schematic of the four placement strategies"
% Author: "Shubham Tiwari"
% Date Started: "2026-07-26"
% Date Updated: "2026-10-14"
%
% Description:
% Example transect (23.3 m) with tall shrub-bordered gaps (0.50 m) and short
% grass-bordered gaps (0.15 m), wind from left to right. Each strategy places
% N = 4 structures at gap midpoints, splitting gaps into shorter sub-gaps. No
% structure is added where it would make a sub-gap shorter than 0.25 m.
%   (a) gaps and vegetation without structures, with gap lengths
%   (b) cell-grid: transect split into N equal cells, one structure in the
%       largest gap section within each cell
%   (c) largest-gap: longest remaining gap first
%   (d) scaled-gap: largest gap length / bordering vegetation height first
%   (e) proportional: structures per gap in proportion to gap length
% Gaps that receive a structure are outlined with a dashed border. The
% placements are calculated with the same rules as 03_build_placement_layouts.py
% (functions at the bottom of this script).
%
% This script was used to create Figure 3 in Tiwari et al.
%
% Inputs:  none (example transect defined below)
% Outputs: output/figures/Fig3_placement_schematic.png and .pdf

clear; clc; close all;

%% Set paths
repo = fileparts(fileparts(fileparts(mfilename('fullpath'))));
figdir = fullfile(repo,'output','figures'); if ~exist(figdir,'dir'), mkdir(figdir); end

%% Settings
FONT = 'Arial'; FS = 10; FS_SM = 9; TXT = [0.10 0.10 0.10];
MIN_SUB = 0.25;   % m, shortest sub-gap a structure can create
CM_H = 0.30;      % drawn structure height (m)
N = 4;            % structures on the transect

COL.shrub = [0.38 0.60 0.32]; COL.grass = [0.68 0.82 0.22]; COL.soil = [0.88 0.82 0.66];
COL.gap = [0.93 0.88 0.75]; COL.cm = [0.12 0.18 0.42]; COL.sel = [0.99 0.94 0.82];
COL.selEdge = [0.80 0.65 0.35]; COL.bracket = [0.55 0.40 0.15]; COL.grid = [0.55 0.55 0.58];

%% Example transect
% Gaps: start (m), end (m), bordering vegetation height (m)
GAPS = [ 0.7,  6.7, 0.50;    % 6.0 m, shrub-bordered (length/height 12.0)
         7.5, 10.4, 0.50;    % 2.9 m, shrub-bordered (5.8)
        11.3, 13.8, 0.15;    % 2.5 m, grass-bordered (16.7)
        14.6, 16.9, 0.15;    % 2.3 m, grass-bordered (15.3)
        17.7, 19.8, 0.15;    % 2.1 m, grass-bordered (14.0)
        20.6, 22.6, 0.15];   % 2.0 m, grass-bordered (13.3)
T = 23.3;   % transect length (m)

% Vegetation: start (m), end (m), height (m), type (1 = shrub, 2 = grass)
veg = [ 0.0,  0.7, 0.50, 1;
        6.7,  7.5, 0.50, 1;
       10.4, 11.0, 0.50, 1;
       11.0, 11.3, 0.15, 2;
       13.8, 14.6, 0.15, 2;
       16.9, 17.7, 0.15, 2;
       19.8, 20.6, 0.15, 2;
       22.6, 23.3, 0.15, 2];

%% Structure positions for each strategy
POS.cellgrid = cell_grid(GAPS(:,1:2),N,T);
POS.largest  = largest_gap(GAPS(:,1:2),N,MIN_SUB);
POS.scaled   = scaled_gap(GAPS,N,MIN_SUB);
POS.prop     = proportional(GAPS(:,1:2),N,MIN_SUB);

%% Figure
fig = figure('Units','inches','Position',[0.5 0.5 11.0 9.0],'Color','w');
tl = tiledlayout(fig,5,1,'TileSpacing','tight','Padding','compact');

panel = {'(a)  Baseline: vegetation and gap structure',                       'baseline';
         '(b)  Cell-grid: one structure per cell (largest within-cell gap)',  'cellgrid';
         '(c)  Largest-gap: longest gap first',                               'largest';
         '(d)  Scaled-gap: largest gap length / bordering-vegetation height', 'scaled';
         '(e)  Proportional: structures per gap \propto gap length',          'prop'};

for p = 1:5
    ax = nexttile(tl); hold(ax,'on');
    strat = panel{p,2}; base = strcmp(strat,'baseline');
    pos = []; if ~base, pos = POS.(strat); end

    % Gaps that receive at least one structure
    sel = [];
    for x = pos, sel(end+1) = find(x>=GAPS(:,1) & x<=GAPS(:,2),1); end %#ok<AGROW>
    sel = unique(sel);

    % Soil strip
    fill(ax,[0 T T 0 0],[-0.07 -0.07 0 0 -0.07],COL.soil,'EdgeColor','none');

    % Gaps, outlined when they receive a structure
    for k = 1:size(GAPS,1)
        g0 = GAPS(k,1); g1 = GAPS(k,2);
        if any(sel==k)
            fill(ax,[g0 g1 g1 g0],[0 0 0.80 0.80],COL.sel,'EdgeColor',COL.selEdge, ...
                'LineStyle','--','LineWidth',0.8,'FaceAlpha',0.85);
        else
            fill(ax,[g0 g1 g1 g0],[0 0 0.80 0.80],COL.gap,'EdgeColor','none','FaceAlpha',0.50);
        end
    end

    % Cell boundaries for cell-grid
    if strcmp(strat,'cellgrid')
        for c = 1:N-1
            plot(ax,[c*T/N c*T/N],[-0.07 0.92],':','Color',COL.grid,'LineWidth',0.9);
        end
        for c = 1:N
            text(ax,(c-0.5)*T/N,0.88,sprintf('cell %d',c),'FontSize',FS_SM-1, ...
                'HorizontalAlignment','center','Color',COL.grid,'FontName',FONT);
        end
    end

    % Vegetation (lighter in the strategy panels)
    th = linspace(0,pi,80);
    for v = 1:size(veg,1)
        x1 = veg(v,1); x2 = veg(v,2); h = veg(v,3); xc = (x1+x2)/2; wv = x2-x1;
        if veg(v,4) == 1
            fc = COL.shrub; ec = COL.shrub*0.65;
            if ~base, fc = fc*0.82+0.18; ec = ec*0.7+0.3; end
            xv = xc+(wv/2)*cos(th); yv = h*sin(th);
            fill(ax,[xv xv(end) xv(1)],[yv 0 0],fc,'EdgeColor',ec,'LineWidth',0.6);
        else
            fc = COL.grass; if ~base, fc = fc*0.82+0.18; end
            for b = 1:5
                fr = b/6; bx = x1+fr*wv; lean = (fr-0.5)*wv*0.4; bh = h*(0.8+0.2*sin(pi*fr));
                fill(ax,[bx-0.03 bx+0.03 bx+lean+0.02 bx+lean-0.02],[0 0 bh bh],fc,'EdgeColor','none');
            end
        end
    end
    plot(ax,[0 T],[0 0],'-','Color',[0.45 0.30 0.12],'LineWidth',1.1);

    % Structures as T-bars, numbered in placement order
    for k = 1:numel(pos)
        plot(ax,[pos(k) pos(k)],[0 CM_H],'-','Color',COL.cm,'LineWidth',2.6);
        plot(ax,[pos(k)-0.26 pos(k)+0.26],[CM_H CM_H],'-','Color',COL.cm,'LineWidth',3.0);
        text(ax,pos(k),CM_H+0.07,sprintf('%d',k),'FontSize',FS_SM,'HorizontalAlignment','center', ...
            'FontWeight','bold','Color',TXT,'FontName',FONT);
    end

    % Gap lengths, wind arrow and legend on the baseline panel
    if base
        lbl = {'6.0 m','2.9 m','2.5 m','2.3 m','2.1 m','2.0 m'}; y0 = 0.60;
        for k = 1:size(GAPS,1)
            xL = GAPS(k,1); xR = GAPS(k,2);
            plot(ax,[xL xR],[y0 y0],'-',[xL xL],[y0-0.03 y0],'-',[xR xR],[y0-0.03 y0],'-', ...
                'Color',COL.bracket,'LineWidth',0.7);
            text(ax,(xL+xR)/2,y0+0.05,lbl{k},'FontSize',FS_SM-1,'HorizontalAlignment','center', ...
                'Color',TXT,'FontName',FONT);
        end
        wc = [0.25 0.35 0.68];
        plot(ax,[3 4.4],[0.34 0.34],'-','Color',wc,'LineWidth',1.6);
        plot(ax,4.4,0.34,'>','Color',wc,'MarkerFaceColor',wc,'MarkerSize',6);
        text(ax,2.7,0.34,'Wind (U)','FontSize',FS,'FontWeight','bold','Color',wc, ...
            'HorizontalAlignment','right','FontName',FONT);

        h = gobjects(1,5);
        h(1) = plot(ax,NaN,NaN,'-','Color',COL.cm,'LineWidth',2.6);
        h(2) = fill(ax,NaN,NaN,COL.sel,'EdgeColor',COL.selEdge,'LineStyle','--');
        h(3) = fill(ax,NaN,NaN,COL.shrub,'EdgeColor',COL.shrub*0.65);
        h(4) = fill(ax,NaN,NaN,COL.grass,'EdgeColor','none');
        h(5) = fill(ax,NaN,NaN,COL.gap,'EdgeColor','none');
        lg = legend(ax,h,{'Roughness structure','Treated gap','Shrub','Grass','Bare gap'}, ...
            'Orientation','horizontal','FontSize',FS_SM,'Box','on','EdgeColor',[0.85 0.85 0.85],'FontName',FONT);
        lg.TextColor = TXT; lg.Position = [0.383 0.915 0.5167 0.0230];
    end

    % Panel label and axes
    text(ax,0.010,0.965,panel{p,1},'Units','normalized','FontSize',FS,'FontWeight','bold', ...
        'VerticalAlignment','top','Color',TXT,'FontName',FONT,'BackgroundColor','w','Margin',1);
    ax.XLim = [-0.5 T+0.5]; ax.YLim = [-0.10 1.06];
    ax.YTick = [0 0.25 0.5]; ax.YTickLabel = {'0','0.25','0.5'}; ax.XTick = 0:5:T;
    ax.FontSize = FS; ax.FontName = FONT; ax.Box = 'off'; ax.TickDir = 'out';
    ax.XColor = [0.3 0.3 0.3]; ax.YColor = [0.3 0.3 0.3]; ax.Layer = 'top'; ax.LineWidth = 0.8;
    if p < 5, ax.XTickLabel = {}; else, xlabel(ax,'Distance along transect (m)','FontSize',FS,'FontName',FONT); end
    ylabel(ax,'Height (m)','FontSize',FS,'FontName',FONT);
end
title(tl,sprintf('Roughness-structure placement strategies  (N = %d; structures split gaps, min sub-gap 0.25 m)',N), ...
    'FontSize',FS+1,'FontWeight','bold','FontName',FONT,'Color',TXT);

%% Save with a small white margin
m = 0.1; P = get(fig,'Position');
set(fig,'PaperUnits','inches','PaperSize',[P(3)+2*m P(4)+2*m],'PaperPosition',[m m P(3) P(4)],'InvertHardcopy','off');
print(fig,fullfile(figdir,'Fig3_placement_schematic.pdf'),'-dpdf','-vector');
print(fig,fullfile(figdir,'Fig3_placement_schematic.png'),'-dpng','-r300');

%% Placement functions
function pos = largest_gap(g,n,minsub)
    % Split the longest gap at its midpoint, n times
    P = g; pos = [];
    for i = 1:n
        [mx,idx] = max(P(:,2)-P(:,1));
        if mx < 2*minsub, break; end
        a = P(idx,1); b = P(idx,2); m = (a+b)/2; pos(end+1) = m; %#ok<AGROW>
        P(idx,:) = []; P = [P; a m; m b];
    end
    pos = sort(pos);
end

function pos = scaled_gap(g,n,minsub)
    % Split the gap with the largest length/height ratio, n times
    P = g(:,1:3); pos = [];
    for i = 1:n
        len = P(:,2)-P(:,1); ratio = len./P(:,3); ratio(len < 2*minsub) = -inf;
        [mx,idx] = max(ratio);
        if ~isfinite(mx), break; end
        a = P(idx,1); b = P(idx,2); H = P(idx,3); m = (a+b)/2; pos(end+1) = m; %#ok<AGROW>
        P(idx,:) = []; P = [P; a m H; m b H];
    end
    pos = sort(pos);
end

function pos = proportional(g,n,minsub)
    % Structures per gap in proportion to gap length (largest remainder)
    len = g(:,2)-g(:,1); share = len/sum(len)*n;
    cap = max(0,floor(len/minsub)-1); k = min(floor(share),cap);
    left = n-sum(k); [~,ord] = sort(share-k,'descend');
    while left > 0
        added = false;
        for i = ord'
            if left <= 0, break; end
            if k(i) < cap(i), k(i) = k(i)+1; left = left-1; added = true; end
        end
        if ~added, break; end
    end
    pos = [];
    for i = 1:size(g,1)
        for j = 1:k(i), pos(end+1) = g(i,1)+len(i)*j/(k(i)+1); end %#ok<AGROW>
    end
    pos = sort(pos);
end

function pos = cell_grid(g,n,T)
    % One structure per cell, at the middle of the largest gap section in the cell
    w = T/n; pos = [];
    for c = 0:n-1
        best = -inf; bx = NaN;
        for k = 1:size(g,1)
            s = max(g(k,1),c*w); e = min(g(k,2),(c+1)*w);
            if (e-s) > best && (e-s) > 0, best = e-s; bx = (s+e)/2; end
        end
        if isfinite(bx), pos(end+1) = bx; end %#ok<AGROW>
    end
    pos = sort(pos);
end
