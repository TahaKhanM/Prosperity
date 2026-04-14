# IMC Prosperity 4 Visualizer

A visualizer for [IMC Prosperity 4](https://prosperity.imc.com/) algorithms. Adapted from [jmerle/imc-prosperity-3-visualizer](https://github.com/jmerle/imc-prosperity-3-visualizer).

## Usage

Load algorithm logs from:
- **File upload**: Drag and drop a `.log` file from the backtester output
- **URL**: Paste a URL to a log file
- **Prosperity API**: Load directly from your Prosperity submissions (requires ID token)

## Compatibility

This visualizer is compatible with output from the [prosperity4bt backtester](../imc-prosperity-4-backtester/). Ensure your algorithm includes the Logger class shown on the home page for full visualizer support.

## Development

1. Install [pnpm](https://pnpm.io/) and [Node.js](https://nodejs.org/) v22+.
2. Clone this repository.
3. Run `pnpm install` to install dependencies.
4. Run `pnpm dev` to start the development server.
5. Run `pnpm build` to build for production.
