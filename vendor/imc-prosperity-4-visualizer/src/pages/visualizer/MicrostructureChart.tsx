import Highcharts from 'highcharts';
import { ReactNode } from 'react';
import { ProsperitySymbol } from '../../models.ts';
import { useStore } from '../../store.ts';
import { getAskColor, getBidColor } from '../../utils/colors.ts';
import { Chart } from './Chart.tsx';

export interface MicrostructureChartProps {
  symbol: ProsperitySymbol;
}

export function MicrostructureChart({ symbol }: MicrostructureChartProps): ReactNode {
  const algorithm = useStore(state => state.algorithm)!;

  const midData: [number, number][] = [];
  const domMidData: [number, number][] = [];
  const vwapData: [number, number][] = [];
  const buyFillData: [number, number][] = [];
  const sellFillData: [number, number][] = [];

  let totalTradeValue = 0;
  let totalTradeVolume = 0;

  for (const row of algorithm.data) {
    const ts = row.state.timestamp;
    const depth = row.state.orderDepths[symbol];
    if (!depth) continue;

    // Mid price from activity logs
    const activityRow = algorithm.activityLogs.find(r => r.timestamp === ts && r.product === symbol);
    if (activityRow) {
      midData.push([ts, activityRow.midPrice]);
    }

    // DOM Mid: volume-weighted mid price from top of book
    const bidPrices = Object.keys(depth.buyOrders)
      .map(Number)
      .sort((a, b) => b - a);
    const askPrices = Object.keys(depth.sellOrders)
      .map(Number)
      .sort((a, b) => a - b);

    if (bidPrices.length > 0 && askPrices.length > 0) {
      const bestBid = bidPrices[0];
      const bestAsk = askPrices[0];
      const bidVol = depth.buyOrders[bestBid];
      const askVol = Math.abs(depth.sellOrders[bestAsk]);
      const totalVol = bidVol + askVol;

      if (totalVol > 0) {
        // DOM mid weights toward side with more volume
        const domMid = (bestBid * askVol + bestAsk * bidVol) / totalVol;
        domMidData.push([ts, domMid]);
      }
    }

    // Running VWAP from own trades
    const ownTrades = row.state.ownTrades[symbol] ?? [];
    for (const trade of ownTrades) {
      totalTradeValue += trade.price * trade.quantity;
      totalTradeVolume += trade.quantity;

      if (trade.buyer === 'SUBMISSION') {
        buyFillData.push([ts, trade.price]);
      } else if (trade.seller === 'SUBMISSION') {
        sellFillData.push([ts, trade.price]);
      }
    }

    if (totalTradeVolume > 0) {
      vwapData.push([ts, totalTradeValue / totalTradeVolume]);
    }
  }

  const series: Highcharts.SeriesOptionsType[] = [
    {
      type: 'line',
      name: 'Mid',
      color: 'rgba(127, 140, 141, 0.6)',
      lineWidth: 1,
      data: midData,
      tooltip: {
        pointFormat: '<span style="color:{point.color}">●</span> Mid: <b>{point.y}</b><br/>',
      },
    },
    {
      type: 'line',
      name: 'DOM Mid (vol-weighted)',
      color: 'rgba(243, 156, 18, 0.9)',
      lineWidth: 1.5,
      data: domMidData,
      tooltip: {
        pointFormat: '<span style="color:{point.color}">●</span> DOM Mid: <b>{point.y:.2f}</b><br/>',
      },
    },
    {
      type: 'line',
      name: 'VWAP (own trades)',
      color: 'rgba(155, 89, 182, 0.9)',
      lineWidth: 1.5,
      dashStyle: 'ShortDash',
      data: vwapData,
      tooltip: {
        pointFormat: '<span style="color:{point.color}">●</span> VWAP: <b>{point.y:.2f}</b><br/>',
      },
    },
    {
      type: 'scatter',
      name: 'Buy fills',
      color: getBidColor(1.0),
      marker: { symbol: 'triangle', radius: 5 },
      data: buyFillData,
      tooltip: {
        pointFormat: '<span style="color:{point.color}">▲</span> Buy @ <b>{point.y}</b><br/>',
      },
    },
    {
      type: 'scatter',
      name: 'Sell fills',
      color: getAskColor(1.0),
      marker: { symbol: 'triangle-down', radius: 5 },
      data: sellFillData,
      tooltip: {
        pointFormat: '<span style="color:{point.color}">▼</span> Sell @ <b>{point.y}</b><br/>',
      },
    },
  ];

  return (
    <Chart
      title={`${symbol} - Microstructure`}
      series={series}
      options={{
        yAxis: {
          opposite: false,
          allowDecimals: true,
        },
      }}
    />
  );
}
