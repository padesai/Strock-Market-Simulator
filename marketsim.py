"""MC2-P1: Market simulator."""

import pandas as pd
import numpy as np
import datetime as dt
import os
from util import get_data, plot_data, get_orders_data_file


def compute_portvals(orders_file = "./orders/orders.csv", start_val = 1000000):

    orders = get_orders_data_file(orders_file);
    orders_data = pd.read_csv(orders);
    orders_data.sort_values(by='Date',inplace=True,ascending=True);

    start_date = orders_data.iloc[0,0];
    end_date = orders_data.iloc[len(orders_data)-1,0];

    adj_close_prices = get_data(['SPY'],pd.date_range(start_date,end_date));
    orders_data_new = orders_data.set_index('Date',inplace=False)
    orders_join  = orders_data_new.join(adj_close_prices);


    adj_close_prices = adj_close_prices.join(orders_data_new);
    adj_close_prices = adj_close_prices[['SPY']]
    adj_close_prices.rename(columns={'SPY': 'Portval'},inplace=True)
    portvals = pd.DataFrame().reindex_like(adj_close_prices);
    cash = start_val;
    equity = 0;
    portval = cash + equity;
    shares_allocation = {};

    daily_cash = pd.DataFrame().reindex_like(adj_close_prices);
    daily_shares_allocation = {};

    df = adj_close_prices.index;
    df1 = orders_join.index;
    i = 0;
    orders_data_index = 0;

    value = df[0];

    while value in df:

        value1 = pd.to_datetime(value).strftime('%Y-%m-%d')
        if (value in df1):

            sd = orders_data.iloc[orders_data_index,0];
            sym = orders_data.iloc[orders_data_index,1];
            order = orders_data.iloc[orders_data_index,2];
            shares = orders_data.iloc[orders_data_index,3];

            adj_close_price = get_data([sym],pd.date_range(sd,sd));
            adj_close_price = adj_close_price[[sym]]

            commission = 9.95;
            if (not np.isnan(adj_close_price.iloc[0,0])):
                if (order == 'SELL'):
                    if (i != 0):
                        cash = daily_cash.iloc[i-1,0];
                    cash += adj_close_price.iloc[0,0]*0.995*shares;
                    cash -= commission;

                    if (i != 0):
                        previous_date = pd.to_datetime(df[i - 1]).strftime('%Y-%m-%d');
                        shares_allocation = daily_shares_allocation[previous_date];
                    shares_allocation_n = shares_allocation.copy();
                    if(shares_allocation_n.has_key(sym)):
                        shares_allocation_n[sym] -= shares;
                    else:
                        shares_allocation_n[sym] = 0-shares;

                if (order == 'BUY'):
                    if (i != 0):
                        cash = daily_cash.iloc[i-1,0];
                    cash -= adj_close_price.iloc[0,0]*1.005*shares;
                    cash -= commission;


                    if (i != 0):
                        previous_date = pd.to_datetime(df[i - 1]).strftime('%Y-%m-%d');
                        shares_allocation = daily_shares_allocation[previous_date];
                    shares_allocation_n = shares_allocation.copy();
                    if(not shares_allocation.has_key(sym)):
                        shares_allocation_n[sym] = shares;
                    else:
                        shares_allocation_n[sym] += shares;

            orders_data_index += 1;

            leverage = sum_of_abs_of_stock_positions(shares_allocation_n,value1) / (compute_equity(shares_allocation_n,value1) + cash);
            if (leverage <= 2.0):

                daily_shares_allocation[value1] = shares_allocation_n;
                daily_cash.set_value(value1, 'Portval',cash);
                equity = compute_equity(shares_allocation_n, value1);
                portval = cash + equity;
                portvals.set_value(sd,'Portval',portval);

            else:
                last_date = pd.to_datetime(df[i-1]).strftime('%Y-%m-%d');
                sa = daily_shares_allocation[last_date];
                daily_shares_allocation[value1] = sa;
                c = daily_cash.iloc[i-1,0];
                daily_cash.set_value(value1, 'Portval',c);
                e = compute_equity(sa, value1);
                p = c + e;
                portvals.set_value(sd,'Portval',p);

            i += 1;

            if (i == len(df)):
                break;

            value = df[i];

        else:
            current_date = value1;

            previous_date = pd.to_datetime(df[i-1]).strftime('%Y-%m-%d');

            next_order_date = pd.to_datetime(df1[orders_data_index]).strftime('%Y-%m-%d');

            new_data = get_data(['SPY'],pd.date_range(current_date,next_order_date));

            l = i + len(new_data)-2;
            b = i;
            date_before_next_order_date = pd.to_datetime(df[l]).strftime('%Y-%m-%d');
            cash_new = daily_cash.iloc[i-1,0];
            shares_allocation_new = daily_shares_allocation[previous_date];

            equity = compute_equity_range(shares_allocation_new, current_date, date_before_next_order_date);
            portvals_intermed = equity + cash_new;
            portvals['Portval'][current_date:date_before_next_order_date] = portvals_intermed;
            daily_cash['Portval'][current_date:date_before_next_order_date] = cash_new;

            for a in range(b, l+1):
                date_assigned = pd.to_datetime(df[a]).strftime('%Y-%m-%d');
                daily_shares_allocation[date_assigned] = shares_allocation_new;

            i = l + 1;
            value = df[i];

    portvals = portvals.groupby(portvals.index).last();

    return portvals

def sum_of_abs_of_stock_positions(share_allocation,start_date):

    total = 0;

    for key,value in share_allocation.iteritems():
        adj_close_pr = get_data([key],pd.date_range(start_date,start_date));
        adj_close_pr = adj_close_pr[[key]];
        total += np.absolute(value*adj_close_pr.iloc[0,0]);

    return total

def compute_equity_range(share_allocation,start_date,end_date):

    keys = share_allocation.keys();
    values = share_allocation.values();

    adj_close_prices = get_data(keys,pd.date_range(start_date,end_date));
    equity = adj_close_prices[keys]*values;
    equity = equity.sum(axis=1)

    return equity

def compute_equity(share_allocation,start_date):

    equity = 0;

    for key,value in share_allocation.iteritems():
        adj_close_pr = get_data([key],pd.date_range(start_date,start_date));
        adj_close_pr = adj_close_pr[[key]];
        equity += value*adj_close_pr.iloc[0,0];

    return equity

def author():
    return 'pdesai75'

def test_code():
    # this is a helper function you can use to test your code
    # note that during autograding his function will not be called.
    # Define input parameters

    of = "orders-leverage-1.csv"
    sv = 1000000

    # Process orders
    portvals = compute_portvals(orders_file = of, start_val = sv)
    if isinstance(portvals, pd.DataFrame):
        portvals = portvals[portvals.columns[0]] # just get the first column
    else:
        "warning, code did not return a DataFrame"
    
    # Get portfolio stats
    # Here we just fake the data. you should use your code from previous assignments.
    start_date = portvals.index.values[0];
    end_date = portvals.index.values[-1];
    cum_ret, avg_daily_ret, std_daily_ret, sharpe_ratio =[0.2,0.01,0.02,1.5]
    cum_ret_SPY, avg_daily_ret_SPY, std_daily_ret_SPY, sharpe_ratio_SPY = [0.2,0.01,0.02,1.5]

    # Compare portfolio against $SPX
    print "Date Range: {} to {}".format(start_date, end_date)
    print
    print "Sharpe Ratio of Fund: {}".format(sharpe_ratio)
    print "Sharpe Ratio of SPY : {}".format(sharpe_ratio_SPY)
    print
    print "Cumulative Return of Fund: {}".format(cum_ret)
    print "Cumulative Return of SPY : {}".format(cum_ret_SPY)
    print
    print "Standard Deviation of Fund: {}".format(std_daily_ret)
    print "Standard Deviation of SPY : {}".format(std_daily_ret_SPY)
    print
    print "Average Daily Return of Fund: {}".format(avg_daily_ret)
    print "Average Daily Return of SPY : {}".format(avg_daily_ret_SPY)
    print
    print "Final Portfolio Value: {}".format(portvals[-1])

if __name__ == "__main__":
    test_code()
