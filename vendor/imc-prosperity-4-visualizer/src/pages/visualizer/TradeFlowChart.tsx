import Highcharts from 'highcharts';
import { ReactNode } from 'react';
import { ProsperitySymbol } from '../../models.ts';
import { useStore } from '../../store.ts';
import { getAskColor, getBidColor } from '../../utils/colors.ts';
import { Chart } from './Chart.tsx';

export interface TradeFlowChartProps {
  symbol: ProsperitySymbol;
}

export function TradeFlowChart({ symbol }: TradeFlowChartProps): ReactNode {
  const algorithm = useStore(state => state.algorithm)!;

  const buyVolumeData: [number, number][] = [];
  const sellVolumeData: [number, number][] = [];
  const netFlowData: [number, number][] = [];
  const cumulativeFlowData: [number, number][] = [];

  let cumulativeNet = 0;

  for (const row of algorithm.data) {
    const ts = row.state.timestamp;
    const ownTrades = row.state.ownTrades[symbol] ?? [];

    let buyVol = 0;
    let sellVol = 0;

    for (const trade of ownTrades) {
      if (trade.buyer === 'SUBMISSION') {
        buyVol += trade.quantity;
      } else if (trade.seller === 'SUBMISSION') {
        sellVol += trade.quantity;
      }
    }

    buyVolumeData.push([ts, buyVol]);
    sellVolumeData.push([ts, -sellVol]);
    netFlowData.push([ts, buyVol - sellVol]);

    cumulativeNet += buyVol - sellVol;
    cumulativeFlowData.push([ts, cumulativeNet]);
  }

  const series: Highcharts.SeriesOptionsType[] = [
    {
      type: 'column',
      name: 'Buy volume',
      color: getBidColor(0.7),
      data: buyVolumeData,
      yAxis: 0,
      tooltip: {
        pointFormat: '<span style="color:{point.color}">●</span> Buys: <b>{point.y}</b><br/>',
      },
    },
    {
      type: 'column',
      name: 'Sell volume',
      color: getAskColor(0.7),
      data: sellVolumeData,
      yAxis: 0,
      tooltip: {
        pointFormat: '<span style="color:{point.color}">●</span> Sells: <b>{point.y}</b><br/>',
      },
    },
    {
      type: 'line',
      name: 'Cumulative net flow',
      color: 'rgba(52, 152, 219, 0.9)',
      lineWidth: 1.5,
      data: cumulativeFlowData,
      yAxis: 1,
      tooltip: {
        pointFormat: '<span style="color:{point.color}">●</span> Cumulative: <b>{point.y}</b><br/>',
      },
    },
  ];

  return (
    <Chart
      title={`${symbol} - Trade Flow`}
      series={series}
      options={{
        yAxis: [
          {
            opposite: false,
            allowDecimals: false,
            title: { text: 'Volume per tick' },
            plotLines: [
              {
                value: 0,
                color: 'rgba(127, 140, 141, 0.4)',
                width: 1,
              },
            ],
          },
          {
            opposite: true,
            allowDecimals: false,
            title: { text: 'Cumulative net' },
          },
        ],
      }}
    />
  );
}
