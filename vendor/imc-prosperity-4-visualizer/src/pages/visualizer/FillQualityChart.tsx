import Highcharts from 'highcharts';
import { ReactNode } from 'react';
import { ProsperitySymbol } from '../../models.ts';
import { useStore } from '../../store.ts';
import { getAskColor, getBidColor } from '../../utils/colors.ts';
import { Chart } from './Chart.tsx';

export interface FillQualityChartProps {
  symbol: ProsperitySymbol;
}

export function FillQualityChart({ symbol }: FillQualityChartProps): ReactNode {
  const algorithm = useStore(state => state.algorithm)!;

  // Build a lookup from timestamp -> mid price
  const midByTimestamp = new Map<number, number>();
  for (const row of algorithm.activityLogs) {
    if (row.product === symbol) {
      midByTimestamp.set(row.timestamp, row.midPrice);
    }
  }

  const edgePerBuyData: [number, number][] = [];
  const edgePerSellData: [number, number][] = [];
  const cumulativeEdgeData: [number, number][] = [];

  let cumulativeEdge = 0;

  for (const row of algorithm.data) {
    const ts = row.state.timestamp;
    const mid = midByTimestamp.get(ts);
    if (mid === undefined) continue;

    const ownTrades = row.state.ownTrades[symbol] ?? [];
    for (const trade of ownTrades) {
      if (trade.buyer === 'SUBMISSION') {
        // Buying: edge = mid - fill price (positive = bought below mid)
        const edge = (mid - trade.price) * trade.quantity;
        edgePerBuyData.push([ts, mid - trade.price]);
        cumulativeEdge += edge;
      } else if (trade.seller === 'SUBMISSION') {
        // Selling: edge = fill price - mid (positive = sold above mid)
        const edge = (trade.price - mid) * trade.quantity;
        edgePerSellData.push([ts, trade.price - mid]);
        cumulativeEdge += edge;
      }
    }

    if (edgePerBuyData.length > 0 || edgePerSellData.length > 0) {
      cumulativeEdgeData.push([ts, cumulativeEdge]);
    }
  }

  const series: Highcharts.SeriesOptionsType[] = [
    {
      type: 'scatter',
      name: 'Buy edge (mid - fill)',
      color: getBidColor(0.8),
      marker: { symbol: 'triangle', radius: 4 },
      data: edgePerBuyData,
      yAxis: 0,
      tooltip: {
        pointFormat: '<span style="color:{point.color}">▲</span> Buy edge: <b>{point.y}</b> vs mid<br/>',
      },
    },
    {
      type: 'scatter',
      name: 'Sell edge (fill - mid)',
      color: getAskColor(0.8),
      marker: { symbol: 'triangle-down', radius: 4 },
      data: edgePerSellData,
      yAxis: 0,
      tooltip: {
        pointFormat: '<span style="color:{point.color}">▼</span> Sell edge: <b>{point.y}</b> vs mid<br/>',
      },
    },
    {
      type: 'line',
      name: 'Cumulative edge (vol-weighted)',
      color: 'rgba(52, 152, 219, 0.9)',
      lineWidth: 2,
      data: cumulativeEdgeData,
      yAxis: 1,
      tooltip: {
        pointFormat: '<span style="color:{point.color}">●</span> Cumulative: <b>{point.y:.0f}</b><br/>',
      },
    },
  ];

  return (
    <Chart
      title={`${symbol} - Fill Quality vs Mid`}
      series={series}
      options={{
        yAxis: [
          {
            opposite: false,
            allowDecimals: true,
            title: { text: 'Edge per fill' },
            plotLines: [
              {
                value: 0,
                color: 'rgba(127, 140, 141, 0.5)',
                width: 1,
                dashStyle: 'Dash',
              },
            ],
          },
          {
            opposite: true,
            allowDecimals: false,
            title: { text: 'Cumulative edge' },
          },
        ],
      }}
    />
  );
}
