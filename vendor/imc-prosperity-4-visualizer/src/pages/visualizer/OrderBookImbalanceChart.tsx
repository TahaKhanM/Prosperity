import Highcharts from 'highcharts';
import { ReactNode } from 'react';
import { ProsperitySymbol } from '../../models.ts';
import { useStore } from '../../store.ts';
import { getAskColor, getBidColor } from '../../utils/colors.ts';
import { Chart } from './Chart.tsx';

export interface OrderBookImbalanceChartProps {
  symbol: ProsperitySymbol;
}

export function OrderBookImbalanceChart({ symbol }: OrderBookImbalanceChartProps): ReactNode {
  const algorithm = useStore(state => state.algorithm)!;

  const bidVolumeData: [number, number][] = [];
  const askVolumeData: [number, number][] = [];
  const imbalanceData: [number, number][] = [];

  for (const row of algorithm.data) {
    const ts = row.state.timestamp;
    const depth = row.state.orderDepths[symbol];
    if (!depth) continue;

    const totalBid = Object.values(depth.buyOrders).reduce((sum, v) => sum + v, 0);
    const totalAsk = Object.values(depth.sellOrders).reduce((sum, v) => sum + Math.abs(v), 0);

    bidVolumeData.push([ts, totalBid]);
    askVolumeData.push([ts, totalAsk]);

    // Imbalance: (bid - ask) / (bid + ask), ranges from -1 to +1
    const total = totalBid + totalAsk;
    if (total > 0) {
      imbalanceData.push([ts, (totalBid - totalAsk) / total]);
    } else {
      imbalanceData.push([ts, 0]);
    }
  }

  const series: Highcharts.SeriesOptionsType[] = [
    {
      type: 'column',
      name: 'Bid volume',
      color: getBidColor(0.6),
      data: bidVolumeData,
      yAxis: 0,
      tooltip: {
        pointFormat: '<span style="color:{point.color}">●</span> Bid vol: <b>{point.y}</b><br/>',
      },
    },
    {
      type: 'column',
      name: 'Ask volume',
      color: getAskColor(0.6),
      data: askVolumeData,
      yAxis: 0,
      tooltip: {
        pointFormat: '<span style="color:{point.color}">●</span> Ask vol: <b>{point.y}</b><br/>',
      },
    },
    {
      type: 'line',
      name: 'Imbalance (B-A)/(B+A)',
      color: 'rgba(243, 156, 18, 0.9)',
      lineWidth: 1.5,
      data: imbalanceData,
      yAxis: 1,
      tooltip: {
        pointFormat: '<span style="color:{point.color}">●</span> Imbalance: <b>{point.y:.3f}</b><br/>',
      },
    },
  ];

  return (
    <Chart
      title={`${symbol} - Order Book Imbalance`}
      series={series}
      options={{
        yAxis: [
          {
            opposite: false,
            allowDecimals: false,
            title: { text: 'Volume' },
          },
          {
            opposite: true,
            allowDecimals: true,
            title: { text: 'Imbalance' },
            min: -1,
            max: 1,
            plotLines: [
              {
                value: 0,
                color: 'rgba(127, 140, 141, 0.5)',
                width: 1,
                dashStyle: 'Dash',
              },
            ],
          },
        ],
      }}
    />
  );
}
