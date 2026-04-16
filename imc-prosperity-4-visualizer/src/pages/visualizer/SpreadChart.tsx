import Highcharts from 'highcharts';
import { ReactNode } from 'react';
import { ProsperitySymbol } from '../../models.ts';
import { useStore } from '../../store.ts';
import { Chart } from './Chart.tsx';

export interface SpreadChartProps {
  symbol: ProsperitySymbol;
}

export function SpreadChart({ symbol }: SpreadChartProps): ReactNode {
  const algorithm = useStore(state => state.algorithm)!;

  const spreadData: [number, number][] = [];
  const spreadPctData: [number, number][] = [];

  for (const row of algorithm.activityLogs) {
    if (row.product !== symbol) {
      continue;
    }

    if (row.bidPrices.length > 0 && row.askPrices.length > 0) {
      const spread = row.askPrices[0] - row.bidPrices[0];
      spreadData.push([row.timestamp, spread]);

      if (row.midPrice > 0) {
        spreadPctData.push([row.timestamp, (spread / row.midPrice) * 10000]);
      }
    }
  }

  const series: Highcharts.SeriesOptionsType[] = [
    {
      type: 'area',
      name: 'Spread (absolute)',
      color: 'rgba(52, 152, 219, 0.8)',
      fillColor: 'rgba(52, 152, 219, 0.15)',
      lineWidth: 1.5,
      data: spreadData,
      yAxis: 0,
      tooltip: {
        pointFormat: '<span style="color:{point.color}">●</span> Spread: <b>{point.y}</b><br/>',
      },
    },
    {
      type: 'line',
      name: 'Spread (bps)',
      color: 'rgba(155, 89, 182, 0.8)',
      lineWidth: 1,
      dashStyle: 'Dot',
      data: spreadPctData,
      yAxis: 1,
      tooltip: {
        pointFormat: '<span style="color:{point.color}">●</span> Spread: <b>{point.y:.1f}</b> bps<br/>',
      },
    },
  ];

  return (
    <Chart
      title={`${symbol} - Spread`}
      series={series}
      options={{
        yAxis: [
          {
            opposite: false,
            allowDecimals: true,
            title: { text: 'Spread' },
            min: 0,
          },
          {
            opposite: true,
            allowDecimals: true,
            title: { text: 'Spread (bps)' },
            min: 0,
          },
        ],
      }}
    />
  );
}
