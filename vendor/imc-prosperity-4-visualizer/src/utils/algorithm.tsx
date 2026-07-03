import { Text } from '@mantine/core';
import { ReactNode } from 'react';
import {
  ActivityLogRow,
  Algorithm,
  AlgorithmDataRow,
  AlgorithmSummary,
  CompressedAlgorithmDataRow,
  CompressedListing,
  CompressedObservations,
  CompressedOrder,
  CompressedOrderDepth,
  CompressedTrade,
  CompressedTradingState,
  ConversionObservation,
  Listing,
  Observation,
  Order,
  OrderDepth,
  Position,
  Product,
  ProsperitySymbol,
  Trade,
  TradingState,
} from '../models.ts';
import { authenticatedAxios } from './axios.ts';

export class AlgorithmParseError extends Error {
  public constructor(public readonly node: ReactNode) {
    super('Failed to parse algorithm logs');
  }
}

interface OfficialPayloadTrade {
  timestamp: number;
  buyer: string;
  seller: string;
  symbol: ProsperitySymbol;
  currency: string;
  price: number;
  quantity: number;
}

interface OfficialPayloadLogRow {
  timestamp: number;
  sandboxLog?: string;
  lambdaLog?: string;
}

interface OfficialPayload {
  submissionId?: string;
  activitiesLog?: string;
  graphLog?: string;
  tradeHistory?: OfficialPayloadTrade[];
  logs?: OfficialPayloadLogRow[];
  profit?: number;
  status?: string;
  positions?: unknown[];
}

function getColumnValues(columns: string[], indices: number[]): number[] {
  const values: number[] = [];

  for (const index of indices) {
    const value = columns[index];
    if (value !== '') {
      values.push(parseFloat(value));
    }
  }

  return values;
}

function parseActivityLogCsv(csvContent: string): ActivityLogRow[] {
  const lines = csvContent.trim().split(/\r?\n/);
  if (lines.length <= 1) {
    return [];
  }

  const rows: ActivityLogRow[] = [];
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i];
    if (!line) {
      continue;
    }
    const columns = line.split(';');

    rows.push({
      day: Number(columns[0]),
      timestamp: Number(columns[1]),
      product: columns[2],
      bidPrices: getColumnValues(columns, [3, 5, 7]),
      bidVolumes: getColumnValues(columns, [4, 6, 8]),
      askPrices: getColumnValues(columns, [9, 11, 13]),
      askVolumes: getColumnValues(columns, [10, 12, 14]),
      midPrice: Number(columns[15]),
      profitLoss: Number(columns[16]),
    });
  }

  return rows;
}

function getActivityLogs(logLines: string[]): ActivityLogRow[] {
  const headerIndex = logLines.indexOf('Activities log:');
  if (headerIndex === -1) {
    return [];
  }

  const csvLines: string[] = [];
  for (let i = headerIndex + 2; i < logLines.length; i++) {
    const line = logLines[i];
    if (line === '') {
      break;
    }
    csvLines.push(line);
  }
  return parseActivityLogCsv(csvLines.join('\n'));
}

function decompressListings(compressed: CompressedListing[]): Record<ProsperitySymbol, Listing> {
  const listings: Record<ProsperitySymbol, Listing> = {};

  for (const [symbol, product, denomination] of compressed) {
    listings[symbol] = {
      symbol,
      product,
      denomination,
    };
  }

  return listings;
}

function decompressOrderDepths(
  compressed: Record<ProsperitySymbol, CompressedOrderDepth>,
): Record<ProsperitySymbol, OrderDepth> {
  const orderDepths: Record<ProsperitySymbol, OrderDepth> = {};

  for (const [symbol, [buyOrders, sellOrders]] of Object.entries(compressed)) {
    orderDepths[symbol] = {
      buyOrders,
      sellOrders,
    };
  }

  return orderDepths;
}

function decompressTrades(compressed: CompressedTrade[]): Record<ProsperitySymbol, Trade[]> {
  const trades: Record<ProsperitySymbol, Trade[]> = {};

  for (const [symbol, price, quantity, buyer, seller, timestamp] of compressed) {
    if (trades[symbol] === undefined) {
      trades[symbol] = [];
    }

    trades[symbol].push({
      symbol,
      price,
      quantity,
      buyer,
      seller,
      timestamp,
    });
  }

  return trades;
}

function decompressObservations(compressed: CompressedObservations): Observation {
  const conversionObservations: Record<Product, ConversionObservation> = {};

  for (const [
    product,
    [bidPrice, askPrice, transportFees, exportTariff, importTariff, sugarPrice, sunlightIndex],
  ] of Object.entries(compressed[1])) {
    conversionObservations[product] = {
      bidPrice,
      askPrice,
      transportFees,
      exportTariff,
      importTariff,
      sugarPrice,
      sunlightIndex,
    };
  }

  return {
    plainValueObservations: compressed[0],
    conversionObservations,
  };
}

function decompressState(compressed: CompressedTradingState): TradingState {
  return {
    timestamp: compressed[0],
    traderData: compressed[1],
    listings: decompressListings(compressed[2]),
    orderDepths: decompressOrderDepths(compressed[3]),
    ownTrades: decompressTrades(compressed[4]),
    marketTrades: decompressTrades(compressed[5]),
    position: compressed[6],
    observations: decompressObservations(compressed[7]),
  };
}

function decompressOrders(compressed: CompressedOrder[]): Record<ProsperitySymbol, Order[]> {
  const orders: Record<ProsperitySymbol, Order[]> = {};

  for (const [symbol, price, quantity] of compressed) {
    if (orders[symbol] === undefined) {
      orders[symbol] = [];
    }

    orders[symbol].push({
      symbol,
      price,
      quantity,
    });
  }

  return orders;
}

function decompressDataRow(compressed: CompressedAlgorithmDataRow, sandboxLogs: string): AlgorithmDataRow {
  return {
    state: decompressState(compressed[0]),
    orders: decompressOrders(compressed[1]),
    conversions: compressed[2],
    traderData: compressed[3],
    algorithmLogs: compressed[4],
    sandboxLogs,
  };
}

function createEmptyObservations(): Observation {
  return {
    plainValueObservations: {},
    conversionObservations: {},
  };
}

function buildTradesByTimestamp(trades: OfficialPayloadTrade[]): Record<number, OfficialPayloadTrade[]> {
  const byTimestamp: Record<number, OfficialPayloadTrade[]> = {};
  for (const trade of trades) {
    if (byTimestamp[trade.timestamp] === undefined) {
      byTimestamp[trade.timestamp] = [];
    }
    byTimestamp[trade.timestamp].push(trade);
  }
  return byTimestamp;
}

function buildPositionsBeforeTimestamp(trades: OfficialPayloadTrade[]): Record<number, Record<Product, Position>> {
  const positions: Record<number, Record<Product, Position>> = {};
  const running: Record<Product, Position> = {};
  const tradesByTimestamp = buildTradesByTimestamp(trades);
  const timestamps = Object.keys(tradesByTimestamp)
    .map(Number)
    .sort((a, b) => a - b);

  for (const timestamp of timestamps) {
    positions[timestamp] = { ...running };
    for (const trade of tradesByTimestamp[timestamp]) {
      if (trade.buyer === 'SUBMISSION') {
        running[trade.symbol] = (running[trade.symbol] ?? 0) + trade.quantity;
      } else if (trade.seller === 'SUBMISSION') {
        running[trade.symbol] = (running[trade.symbol] ?? 0) - trade.quantity;
      }
    }
  }

  return positions;
}

function buildListings(activityLogs: ActivityLogRow[]): Record<ProsperitySymbol, Listing> {
  const listings: Record<ProsperitySymbol, Listing> = {};
  for (const row of activityLogs) {
    if (listings[row.product] !== undefined) {
      continue;
    }
    listings[row.product] = {
      symbol: row.product,
      product: row.product,
      denomination: 'XIRECS',
    };
  }
  return listings;
}

function activityLogOrderDepth(rows: ActivityLogRow[]): Record<ProsperitySymbol, OrderDepth> {
  const orderDepths: Record<ProsperitySymbol, OrderDepth> = {};
  for (const row of rows) {
    const buyOrders: Record<number, number> = {};
    const sellOrders: Record<number, number> = {};
    row.bidPrices.forEach((price, i) => {
      buyOrders[price] = row.bidVolumes[i];
    });
    row.askPrices.forEach((price, i) => {
      sellOrders[price] = -row.askVolumes[i];
    });
    orderDepths[row.product] = { buyOrders, sellOrders };
  }
  return orderDepths;
}

function convertOfficialTrade(trade: OfficialPayloadTrade): Trade {
  return {
    symbol: trade.symbol,
    price: trade.price,
    quantity: trade.quantity,
    buyer: trade.buyer,
    seller: trade.seller,
    timestamp: trade.timestamp,
  };
}

function summarizeOfficialRowTrades(trades: OfficialPayloadTrade[]): string {
  if (trades.length === 0) {
    return '';
  }

  const lines = ['Official payload trades at this timestamp:'];
  for (const trade of trades) {
    const side =
      trade.buyer === 'SUBMISSION'
        ? 'submission buy'
        : trade.seller === 'SUBMISSION'
          ? 'submission sell'
          : 'external';
    lines.push(`${trade.symbol} | ${side} | px=${trade.price} | qty=${trade.quantity}`);
  }
  return lines.join('\n');
}

function parseOfficialAlgorithm(payload: OfficialPayload, summary?: AlgorithmSummary): Algorithm {
  if (!payload.activitiesLog) {
    throw new AlgorithmParseError(<Text>Official payload is missing `activitiesLog`.</Text>);
  }

  const activityLogs = parseActivityLogCsv(payload.activitiesLog);
  const listings = buildListings(activityLogs);
  const trades = payload.tradeHistory ?? [];
  const tradesByTimestamp = buildTradesByTimestamp(trades);
  const positionsBeforeTimestamp = buildPositionsBeforeTimestamp(trades);
  const logRowsByTimestamp: Record<number, OfficialPayloadLogRow> = {};
  for (const row of payload.logs ?? []) {
    logRowsByTimestamp[row.timestamp] = row;
  }

  const activityRowsByTimestamp: Record<number, ActivityLogRow[]> = {};
  for (const row of activityLogs) {
    if (activityRowsByTimestamp[row.timestamp] === undefined) {
      activityRowsByTimestamp[row.timestamp] = [];
    }
    activityRowsByTimestamp[row.timestamp].push(row);
  }

  const timestamps = Object.keys(activityRowsByTimestamp)
    .map(Number)
    .sort((a, b) => a - b);

  const data: AlgorithmDataRow[] = timestamps.map(timestamp => {
    const rows = activityRowsByTimestamp[timestamp];
    const orderDepths = activityLogOrderDepth(rows);
    const timestampTrades = tradesByTimestamp[timestamp] ?? [];
    const ownTrades: Record<ProsperitySymbol, Trade[]> = {};
    const marketTrades: Record<ProsperitySymbol, Trade[]> = {};

    for (const trade of timestampTrades) {
      const target = trade.buyer === 'SUBMISSION' || trade.seller === 'SUBMISSION' ? ownTrades : marketTrades;
      if (target[trade.symbol] === undefined) {
        target[trade.symbol] = [];
      }
      target[trade.symbol].push(convertOfficialTrade(trade));
    }

    return {
      state: {
        timestamp,
        traderData: '',
        listings,
        orderDepths,
        ownTrades,
        marketTrades,
        position: positionsBeforeTimestamp[timestamp] ?? {},
        observations: createEmptyObservations(),
      },
      orders: {},
      conversions: 0,
      traderData: '',
      algorithmLogs: summarizeOfficialRowTrades(timestampTrades),
      sandboxLogs: logRowsByTimestamp[timestamp]?.sandboxLog?.trim?.() ?? '',
    };
  });

  return {
    summary,
    sourceFormat: 'official',
    activityLogs,
    data,
  };
}

function getAlgorithmData(logLines: string[]): AlgorithmDataRow[] {
  const headerIndex = logLines.indexOf('Sandbox logs:');
  if (headerIndex === -1) {
    return [];
  }

  const rows: AlgorithmDataRow[] = [];
  let nextSandboxLogs = '';

  const sandboxLogPrefix = '  "sandboxLog": ';
  const lambdaLogPrefix = '  "lambdaLog": ';

  for (let i = headerIndex + 1; i < logLines.length; i++) {
    const line = logLines[i];
    if (line.endsWith(':')) {
      break;
    }

    if (line.startsWith(sandboxLogPrefix)) {
      nextSandboxLogs = JSON.parse(line.substring(sandboxLogPrefix.length, line.length - 1)).trim();

      if (nextSandboxLogs.startsWith('Conversion request')) {
        const lastRow = rows[rows.length - 1];
        lastRow.sandboxLogs += (lastRow.sandboxLogs.length > 0 ? '\n' : '') + nextSandboxLogs;

        nextSandboxLogs = '';
      }

      continue;
    }

    if (!line.startsWith(lambdaLogPrefix) || line === '  "lambdaLog": "",') {
      continue;
    }

    const start = line.indexOf('[[');
    const end = line.lastIndexOf(']') + 1;

    try {
      const compressedDataRow = JSON.parse(JSON.parse('"' + line.substring(start, end) + '"'));
      rows.push(decompressDataRow(compressedDataRow, nextSandboxLogs));
    } catch (err) {
      console.log(line);
      console.error(err);

      throw new AlgorithmParseError(
        (
          <>
            <Text>Logs are in invalid format. Could not parse the following line:</Text>
            <Text>{line}</Text>
          </>
        ),
      );
    }
  }

  return rows;
}

export function parseAlgorithmLogs(logs: string, summary?: AlgorithmSummary): Algorithm {
  const trimmed = logs.trim();

  try {
    const parsed = JSON.parse(trimmed) as OfficialPayload;
    if (parsed.activitiesLog !== undefined) {
      return parseOfficialAlgorithm(parsed, summary);
    }
  } catch {
    // Fall through to logger-style parsing.
  }

  const logLines = trimmed.split(/\r?\n/);

  const activityLogs = getActivityLogs(logLines);
  const data = getAlgorithmData(logLines);

  if (activityLogs.length === 0 && data.length === 0) {
    throw new AlgorithmParseError(
      (
        <Text>
          Logs are empty, either something went wrong with your submission or your backtester logs in a different format
          than Prosperity&apos;s submission environment.
        </Text>
      ),
    );
  }

  if (activityLogs.length === 0 || data.length === 0) {
    throw new AlgorithmParseError(
      /* prettier-ignore */
      <Text>Logs are in invalid format.</Text>,
    );
  }

  return {
    summary,
    sourceFormat: 'logger',
    activityLogs,
    data,
  };
}

export async function getAlgorithmLogsUrl(algorithmId: string): Promise<string> {
  const urlResponse = await authenticatedAxios.get(
    `https://bz97lt8b1e.execute-api.eu-west-1.amazonaws.com/prod/submission/logs/${algorithmId}`,
  );

  return urlResponse.data;
}

function downloadFile(url: string): void {
  const link = document.createElement('a');
  link.href = url;
  link.download = new URL(url).pathname.split('/').pop()!;
  link.target = '_blank';
  link.rel = 'noreferrer';

  document.body.appendChild(link);
  link.click();
  link.remove();
}

export async function downloadAlgorithmLogs(algorithmId: string): Promise<void> {
  const logsUrl = await getAlgorithmLogsUrl(algorithmId);
  downloadFile(logsUrl);
}

export async function downloadAlgorithmResults(algorithmId: string): Promise<void> {
  const detailsResponse = await authenticatedAxios.get(
    `https://bz97lt8b1e.execute-api.eu-west-1.amazonaws.com/prod/results/tutorial/${algorithmId}`,
  );

  downloadFile(detailsResponse.data.algo.summary.activitiesLog);
}
