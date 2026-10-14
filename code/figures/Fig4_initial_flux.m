% Title: "Initial sediment flux and vegetation structure"
% Author: "Shubham Tiwari"
% Date Started: "2026-07-24"
% Date Updated: "2026-10-14"
%
% Description:
% Modeled horizontal sediment flux without structures at 16 m/s.
% (a) Lorenz curve of flux
% across plots, (b) share of flux from the 10% and 20%
% of plots with the highest flux in each vegetation type, (c) Spearman rank
% correlations between initial flux and plot vegetation indicators. Scaled gap is
% the plot mean of gap length / bordering height (02_gap_heights.py).
% The Gini coefficient is printed but not shown on the figure.
%
% This script was used to create Figure 4 in Tiwari et al.
%
% Inputs:  data/baseline_flux.csv, data/study_plots.csv
% Outputs: output/figures/Fig4_initial_flux.png

clear; clc; close all;

%% Set paths
repo = fileparts(fileparts(fileparts(mfilename('fullpath'))));
figdir = fullfile(repo,'output','figures'); if ~exist(figdir,'dir'), mkdir(figdir); end

%% Load data
B = readtable(fullfile(repo,'data','baseline_flux.csv'),'TextType','string');
S = readtable(fullfile(repo,'data','study_plots.csv'),'TextType','string');

types = ["grass","mixed","shrub"]; tlab = ["Grass","Mixed","Shrub"];
set(groot,'defaultAxesFontName','Helvetica','defaultTextFontName','Helvetica', ...
    'defaultAxesFontSize',10,'defaultAxesLineWidth',1.0,'defaultAxesTitleFontWeight','bold');

% Initial flux at 16 m/s for each plot
B16 = B(B.wind_speed==16,:);
[tf,loc] = ismember(S.plot_id,B16.plot_id);
S.f16 = nan(height(S),1); S.f16(tf) = B16.hflux_gmd(loc(tf));

%% Concentration of flux
f = sort(S.f16(~isnan(S.f16))); n = numel(f);
Lc = cumsum(f)/sum(f); pp = (1:n)/n;
gini = (2*sum((1:n)'.*f)/(n*sum(f))) - (n+1)/n;
top20 = 100*sum(f(ceil(0.8*n):end))/sum(f);
fprintf('Gini = %.2f | top 20%% of plots = %.0f%% of flux\n',gini,top20);

fig = figure('Color','w','Position',[40 40 1300 410]);
tl = tiledlayout(fig,1,3,'Padding','compact','TileSpacing','compact');

%% (a) Lorenz curve
nexttile; hold on;
fill([0 pp 1],[0 Lc' 1],[0.85 0.90 0.95],'EdgeColor','none');
plot(pp,Lc,'-','Color',[0.18 0.43 0.66],'LineWidth',2);
plot([0 1],[0 1],'k--'); box on; grid on; xlim([0 1]); ylim([0 1]);
xlabel('Cumulative fraction of plots'); ylabel('Cumulative fraction of flux');
title('a. Flux concentration across plots');
text(0.06,0.88,sprintf('top 20%% of plots\n= %.0f%% of flux',top20),'FontSize',10);

%% (b) Share of flux from the highest-flux plots
nexttile; hold on;
top = zeros(3,2);
for j = 1:3
    x = sort(S.f16(S.veg_type==types(j) & ~isnan(S.f16))); m = numel(x);
    top(j,1) = 100*sum(x(ceil(0.9*m):end))/sum(x);
    top(j,2) = 100*sum(x(ceil(0.8*m):end))/sum(x);
end
hb = bar(top); hb(1).FaceColor = [0.30 0.45 0.65]; hb(2).FaceColor = [0.72 0.80 0.90];
set(gca,'XTick',1:3,'XTickLabel',tlab); box on; grid on; ylim([0 80]);
ylabel('Flux in most-erosive plots (%)');
legend({'top 10% of plots','top 20% of plots'},'Location','northeast','Box','off','FontSize',10);
title('b. Flux share of most-erosive plots');

%% (c) Spearman correlations with vegetation indicators
nexttile;
vars = {'foliar_cover_pct','veg_height_cm','large_gap_cover_pct','n_canopy_gaps','mean_scaled_gap'};
vlab = {'Cover','Height','Large-gap','No. gaps','Scaled gap'};
rho = zeros(numel(vars),1);
for k = 1:numel(vars), rho(k) = spearman(S.f16,S.(vars{k})); end
[rs,oi] = sort(rho); hb = barh(rs); hb.FaceColor = 'flat';
for k = 1:numel(rs)
    if rs(k) >= 0, hb.CData(k,:) = [0.75 0.22 0.17]; else, hb.CData(k,:) = [0.18 0.43 0.66]; end
end
set(gca,'YTick',1:numel(vars),'YTickLabel',vlab(oi)); box on; grid on; xlim([-0.8 0.8]);
xlabel('Rank correlation with baseline flux (\rho)');
title('c. Correlates of baseline flux');
disp(table(vlab(oi)',rs,'VariableNames',{'indicator','rho'}))

exportgraphics(fig,fullfile(figdir,'Fig4_initial_flux.png'),'Resolution',300);

%% Spearman correlation without the Statistics Toolbox
function r = spearman(a,b)
    m = ~isnan(a) & ~isnan(b); ra = tierank(a(m)); rb = tierank(b(m));
    ra = ra-mean(ra); rb = rb-mean(rb);
    r = sum(ra.*rb)/sqrt(sum(ra.^2)*sum(rb.^2));
end
function rk = tierank(x)
    [~,ord] = sort(x); rk = zeros(size(x)); rk(ord) = 1:numel(x);
    [u,~,ic] = unique(x);
    for k = 1:numel(u), i = ic==k; if sum(i)>1, rk(i) = mean(rk(i)); end, end
end
