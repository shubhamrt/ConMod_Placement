% Title: "Map and vegetation structure of the study plots"
% Author: "Shubham Tiwari"
% Date Started: "2026-07-13"
% Date Updated: "2026-10-14"
%
% Description:
% (a) Map of the 1,500 study plots (500 grass, 500 mixed, 500 shrub) over all
% unique AIM plot locations in the western US (grey). (b-d) Mean canopy gap
% length, total foliar cover and vegetation height by vegetation type, shown as
% violins with the 25-75th percentile box, 10-90th percentile whiskers and median.
% State outlines need the Mapping Toolbox; without it the map is drawn without them.
%
% This script was used to create Figure 2 in Tiwari et al.
%
% Inputs:  data/study_plots.csv, data/map_background_plots.csv
% Outputs: output/figures/Fig2_study_plots.png

clear; clc; close all;

%% Set paths (run from anywhere)
repo = fileparts(fileparts(fileparts(mfilename('fullpath'))));
figdir = fullfile(repo,'output','figures'); if ~exist(figdir,'dir'), mkdir(figdir); end

%% Load data
sel  = readtable(fullfile(repo,'data','study_plots.csv'),'TextType','string');
allp = readtable(fullfile(repo,'data','map_background_plots.csv'));

types = {'grass','mixed','shrub'}; labels = {'Grass','Mixed','Shrub'};
COL = struct('grass',[0.18 0.63 0.37],'mixed',[0.19 0.51 0.74],'shrub',[0.90 0.63 0.12]);
GREY = [0.74 0.74 0.74]; STATE = [0.60 0.60 0.60];
FT = 'Helvetica'; FS = 11;
set(groot,'defaultAxesFontName',FT,'defaultTextFontName',FT,'defaultAxesFontSize',FS,'defaultTextFontSize',FS);
XL = [-125 -100]; YL = [31 49];

fig = figure('Color','w','Units','pixels','Position',[20 20 1500 1050]);

%% (a) Map
axA = axes('Units','normalized','Position',[0.045 0.070 0.545 0.880]); hold(axA,'on');
try
    st = shaperead('usastatelo','UseGeoCoords',true);
    for i = 1:numel(st)
        plot(axA,st(i).Lon,st(i).Lat,'-','Color',STATE,'LineWidth',0.7,'HandleVisibility','off');
    end
catch
    disp('Mapping Toolbox not found, state outlines skipped')
end

% All AIM plot locations
scatter(axA,allp.longitude,allp.latitude,3,'o','filled','MarkerFaceColor',[0.76 0.76 0.76], ...
    'MarkerFaceAlpha',0.22,'MarkerEdgeColor','none','HandleVisibility','off');

% Study plots by vegetation type
for k = 1:3
    d = sel(sel.veg_type==types{k},:);
    scatter(axA,d.longitude,d.latitude,20,'o','filled','MarkerFaceColor',COL.(types{k}), ...
        'MarkerFaceAlpha',0.88,'MarkerEdgeColor',COL.(types{k})*0.58,'LineWidth',0.35,'HandleVisibility','off');
end
xlim(axA,XL); ylim(axA,YL); daspect(axA,[1 cosd(mean(YL)) 1]);
axA.LineWidth = 1.2; axA.Layer = 'top'; box(axA,'on');
axA.XTick = -125:5:-100; axA.YTick = 30:5:50;
axA.XTickLabel = compose('%d\\circ',abs(axA.XTick))+"W";
axA.YTickLabel = compose('%d\\circ',axA.YTick)+"N";
axA.FontSize = FS-1;
grid(axA,'on'); axA.GridColor = [0.85 0.85 0.85]; axA.GridAlpha = 0.7;
xlabel(axA,'Longitude'); ylabel(axA,'Latitude');
t = title(axA,'a. Spatial distribution of study plots over the western United States','FontSize',FS,'FontWeight','bold');
t.Position(2) = 49.2;

% North arrow
nax = XL(1)+0.05*diff(XL); nay = YL(2)-0.13*diff(YL); nl = diff(YL)*0.06;
patch(axA,[nax nax-nl*0.18 nax],[nay+nl nay nay+nl*0.4],[0.1 0.1 0.1],'EdgeColor','none','HandleVisibility','off');
patch(axA,[nax nax+nl*0.18 nax],[nay+nl nay nay+nl*0.4],[0.95 0.95 0.95],'EdgeColor',[0.15 0.15 0.15],'LineWidth',0.6,'HandleVisibility','off');
text(axA,nax,nay+nl*1.35,'N','FontSize',FS,'FontWeight','bold','HorizontalAlignment','center');

% Legend
h = gobjects(1,4);
for k = 1:3
    h(k) = scatter(axA,NaN,NaN,40,'o','filled','MarkerFaceColor',COL.(types{k}),'MarkerEdgeColor','k','LineWidth',0.3);
end
h(4) = scatter(axA,NaN,NaN,10,'o','filled','MarkerFaceColor',GREY,'MarkerEdgeColor','none');
nbg = regexprep(num2str(height(allp)),'\d{1,3}(?=(\d{3})+(?!\d))','$0,');
lg = legend(axA,h,{sprintf('Grass (n = %d)',sum(sel.veg_type=="grass")), ...
    sprintf('Mixed (n = %d)',sum(sel.veg_type=="mixed")), ...
    sprintf('Shrub (n = %d)',sum(sel.veg_type=="shrub")), ...
    sprintf('All AIM plots (n = %s)',nbg)},'FontSize',FS-1,'Location','southwest');
lg.Box = 'off'; lg.Color = 'none'; lg.ItemTokenSize = [14 14];

%% (b) Mean canopy gap length
axB = axes('Units','normalized','Position',[0.640 0.690 0.220 0.250]);
violin_by_type(axB,sel,'mean_gap_length_m',types,labels,COL);
ylabel(axB,'Mean canopy gap length (m)');
yl = prctile(sel.mean_gap_length_m,99.5); ylim(axB,[0 max(1.5,ceil(yl*2)/2)]);
axB.FontSize = FS-1; title(axB,'b. Canopy gap size','FontWeight','bold','FontSize',FS);

%% (c) Foliar cover
axC = axes('Units','normalized','Position',[0.640 0.380 0.220 0.250]);
violin_by_type(axC,sel,'foliar_cover_pct',types,labels,COL);
ylabel(axC,'Total foliar cover (%)'); ylim(axC,[0 100]);
axC.FontSize = FS-1; title(axC,'c. Vegetation cover','FontWeight','bold','FontSize',FS);

%% (d) Vegetation height
axD = axes('Units','normalized','Position',[0.640 0.060 0.220 0.250]);
violin_by_type(axD,sel,'veg_height_cm',types,labels,COL);
ylabel(axD,'Vegetation height (cm)');
yl = prctile(sel.veg_height_cm,99.5); ylim(axD,[0 max(20,ceil(yl/10)*10)]);
axD.FontSize = FS-1; title(axD,'d. Vegetation height','FontWeight','bold','FontSize',FS);

%% Save with a white border
fontname(fig,FT);
tmp = [tempname '.png']; exportgraphics(fig,tmp,'Resolution',300);
img = imread(tmp); img = padarray(img,[20 20],255,'both');
imwrite(img,fullfile(figdir,'Fig2_study_plots.png'));

%% Violin plot function
function violin_by_type(ax,sel,col,types,labels,COL)
    hold(ax,'on'); rng(42,'twister');
    for k = 1:numel(types)
        v = sel.(col)(sel.veg_type==types{k}); v = v(isfinite(v));
        if isempty(v), continue; end
        c = COL.(types{k}); cd = c*0.62;

        % Density outline (histogram if Statistics Toolbox is missing)
        if exist('ksdensity','file') == 2
            [f,xi] = ksdensity(v,'NumPoints',200);
        else
            nb = max(15,min(35,round(sqrt(numel(v)))));
            [N,E] = histcounts(v,linspace(min(v),max(v),nb+1),'Normalization','pdf');
            xi = linspace(min(v),max(v),200);
            f = interp1((E(1:end-1)+E(2:end))/2,movmean(N,3),xi,'pchip',0);
        end
        f = f(:)'; xi = xi(:)'; hw = 0.32*f./max(f);
        patch(ax,[k-hw fliplr(k+hw)],[xi fliplr(xi)],c,'FaceAlpha',0.14,'EdgeColor','none');

        % A sample of individual plots
        n = min(150,numel(v)); idx = randperm(numel(v),n);
        scatter(ax,k+(rand(n,1)-0.5)*0.28,v(idx),7,'o','filled','MarkerFaceColor',c, ...
            'MarkerFaceAlpha',0.14,'MarkerEdgeColor','none');

        % Whiskers (10-90th), box (25-75th) and median
        q = prctile(v,[10 25 50 75 90]); bw = 0.28;
        plot(ax,[k k],q([1 5]),'-','Color',cd,'LineWidth',1.2);
        plot(ax,[k-0.07 k+0.07],[q(1) q(1)],'-','Color',cd,'LineWidth',1.2);
        plot(ax,[k-0.07 k+0.07],[q(5) q(5)],'-','Color',cd,'LineWidth',1.2);
        patch(ax,[k-bw/2 k+bw/2 k+bw/2 k-bw/2],[q(2) q(2) q(4) q(4)],c+(1-c)*0.72, ...
            'FaceAlpha',0.92,'EdgeColor',c,'LineWidth',1.25);
        plot(ax,[k-bw/2 k+bw/2],[q(3) q(3)],'-','Color',cd,'LineWidth',2.0);
    end
    ax.XTick = 1:numel(types); ax.XTickLabel = labels; xlim(ax,[0.4 numel(types)+0.6]);
    ax.LineWidth = 1.1; ax.Layer = 'top'; box(ax,'on');
    ax.YGrid = 'on'; ax.XGrid = 'off'; ax.GridColor = [0.88 0.88 0.88]; ax.GridAlpha = 0.45;
end
