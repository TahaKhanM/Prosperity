import Highcharts from 'highcharts';
import { ReactNode } from 'react';
import { ProsperitySymbol } from '../../models.ts';
import { useStore } from '../../store.ts';
import { getAskColor, getBidColor } from '../../utils/colors.ts';
import { Chart } from './Chart.tsx';

export interface ProductPriceChartProps {
  symbol: ProsperitySymbol;
}

export function ProductPriceChart({ symbol }: ProductPriceChartProps): ReactNode {
  const algorithm = useStore(state => state.algorithm)!;

  const series: Highcharts.SeriesOptionsType[] = [
    { type: 'line', name: 'Bid 3', color: getBidColor(0.5), marker: { symbol: 'square' }, data: [] },
    { type: 'line', name: 'Bid 2', color: getBidColor(0.75), marker: { symbol: 'circle' }, data: [] },
    { type: 'line', name: 'Bid 1', color: getBidColor(1.0), marker: { symbol: 'triangle' }, data: [] },
    { type: 'line', name: 'Mid price', color: 'gray', dashStyle: 'Dash', marker: { symbol: 'diamond' }, data: [] },
    { type: 'line', name: 'Ask 1', color: getAskColor(1.0), marker: { symbol: 'triangle-down' }, data: [] },
    { type: 'line', name: 'Ask 2', color: getAskColor(0.75), marker: { symbol: 'circle' }, data: [] },
    { type: 'line', name: 'Ask 3', color: getAskColor(0.5), marker: { symbol: 'square' }, data: [] },
    {
      type: 'scatter',
      name: 'Submission buys',
      color: getBidColor(1.0),
      marker: { symbol: 'triangle', radius: 4 },
      data: [],
      tooltip: { pointFormat: '<span style="color:{point.color}">●</span> Submission buy @ <b>{point.y}</b><br/>' },
    },
    {
      type: 'scatter',
      name: 'Submission sells',
      color: getAskColor(1.0),
      marker: { symbol: 'triangle-down', radius: 4 },
      data: [],
      tooltip: { pointFormat: '<span style="color:{point.color}">●</span> Submission sell @ <b>{point.y}</b><br/>' },
    },
    {
      type: 'scatter',
      name: 'External trades',
      color: '#c0c0c0',
      marker: { symbol: 'diamond', radius: 3 },
      data: [],
      tooltip: { pointFormat: '<span style="color:{point.color}">●</span> External trade @ <b>{point.y}</b><br/>' },
    },
  ];

  for (const row of algorithm.activityLogs) {
    if (row.product !== symbol) {
      continue;
    }

    for (let i = 0; i < row.bidPrices.length; i++) {
      (series[2 - i] as any).data.push([row.timestamp, row.bidPrices[i]]);
    }

    (series[3] as any).data.push([row.timestamp, row.midPrice]);

    for (let i = 0; i < row.askPrices.length; i++) {
      (series[i + 4] as any).data.push([row.timestamp, row.askPrices[i]]);
    }
  }

  for (const row of algorithm.data) {
    const ownTrades = row.state.ownTrades[symbol] ?? [];
    for (const trade of ownTrades) {
      if (trade.buyer === 'SUBMISSION') {
        (series[7] as any).data.push([trade.timestamp, trade.price]);
      } else if (trade.seller === 'SUBMISSION') {
        (series[8] as any).data.push([trade.timestamp, trade.price]);
      }
    }

    const marketTrades = row.state.marketTrades[symbol] ?? [];
    for (const trade of marketTrades) {
      (series[9] as any).data.push([trade.timestamp, trade.price]);
    }
  }

  return <Chart title={`${symbol} - Price`} series={series} />;
}
