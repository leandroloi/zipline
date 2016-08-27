import dateutil
import logging

from zipline import TradingAlgorithm
from zipline.api import order_target, record, symbol
from zipline.data import load_from_yahoo
from zipline.finance import commission
from zipline.finance.slippage import FixedSlippage


logging.basicConfig(level=logging.DEBUG)


s = 'AAPL'

# initialize algorithm
def initialize(context):
    logging.debug('enter initialize')
    context.set_slippage(FixedSlippage())
    context.set_commission(commission.PerTrade(cost=16))
    context.i = 0
    context.sym = symbol(s)

def handle_data(context, data):
    # Skip first 300 days to get full windows
    context.i += 1
    if context.i < 300:
        return

    # Compute averages
    # history() has to be called with the same params
    # from above and returns a pandas dataframe.
    short_df = data.history(context.sym, 'price', 100, '1d')
    print(short_df.tail())
    short_mavg = short_df.dropna()
    print(short_mavg.tail())
    short_mavg = short_mavg.mean()

    long_df = data.history(context.sym, 'price', 300, '1d')
    print(long_df.tail())
    long_mavg = short_df.dropna()
    print(long_mavg.tail())
    long_mavg = long_mavg.mean()

    #long_mavg = data.history(context.sym, 'price', 300, '1d').dropna().mean()

    # Trading logic
    if short_mavg > long_mavg:
        # order_target orders as many shares as needed to
        # achieve the desired number of shares.
        order_target(context.sym, 100)
    elif short_mavg < long_mavg:
        order_target(context.sym, 0)

    # Save values for later inspection
    record(AAPL=data.current(context.sym, "price"),
           short_mavg=short_mavg,
           long_mavg=long_mavg)


if __name__ == '__main__':
    logging.debug('run_algorithm begin')
    # dates
    start = dateutil.parser.parse('20160118')
    end = dateutil.parser.parse('20160701')
    security = [s]
    data = load_from_yahoo(stocks=security, indexes={}, start=start, end=end, adjusted=False)
    logging.debug('done loading from yahoo. {} {} {}'.format(
        security, start,end))


    # create and run algorithm
    algo = TradingAlgorithm(
        initialize=initialize,
        handle_data=handle_data,
        capital_base=10000)
    algo.security = security
    logging.debug('starting to run algo...')
    results = algo.run(data)

    logging.debug('done running algo')