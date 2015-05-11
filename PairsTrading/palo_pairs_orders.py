
# Python imports
import time
import datetime as dt

# 3rd party imports
import numpy as np
import pandas as pd

# LRL imports
import lrlsql as lrlsq
import lrlutil as lrlu
import lrlbacktester as lrlbtr
import lrlstrat as lrls
import lrllearn as lrll
import lrlfeatures as lrlf


def trade_lr_pairs():
    # Strategy arameter to manipulate
    dt_start = dt.datetime(2009, 1, 1, 16)
    dt_end = dt.datetime(2009, 12, 31, 16)
    s_list = 'S&P 500'
    i_lookback = 252
    i_max_holding = 20

    # Backtester parameters
    f_cash_cent = 0.2 # Percent cash allocated to each event
    i_max_equities = 100.0 # Max equites to trade at one point
    f_slippage = 0.0005
    f_minimumcommision = 2.95
    f_commision_share = 0.0035
    i_target_leverage = 1.
    f_borrow_rate = 0.015
    f_stop_loss = 1.0

    # Access data
    ls_syms = lrlsq.lsq_list(s_list)
    ls_keys = ['open', 'close']
    dt_data_start = lrlu.get_nyse_offset(dt_start, -i_lookback+1)
    ldfData = lrlsq.lsq_data(dt_data_start, dt_end, ls_syms, ls_keys, b_hard=False)
    d_data = dict(zip(ls_keys, ldfData))
    df_open = d_data['open']
    df_close = d_data['close']
    df_ln = np.log(df_close)

    # Generate orders   
    print 'Generating Orders'
    df_holding = pd.DataFrame(index = [0], columns = df_ln.columns).fillna(0.0)
    ddt_lt_syms = {}
    for i_date, dt_date in enumerate(df_ln.index[i_lookback:]):
        # read df_pairs from pkl
        s_filename = 'selected' + str(hash(dt_date)) + '.pkl'
        df_pairs = lrlu.cache_get(s_filename)
        if type(df_pairs) == type(None):
            print 'No pkl files'
            exit()
        # generate orders
        ls_orders = []
        for i_tmp, i_pairs in enumerate(df_pairs.index):
            s_sym = df_pairs['pairs'][i_pairs][0]
            s_pair = df_pairs['pairs'][i_pairs][1]
            # check if the pairs are holded
            if df_holding[s_sym] > 0 or df_holding[s_pair] > 0:
                continue
            # get X, Y values and residuals information
            na_x = df_ln[s_sym][i_date:i_date+i_lookback].values
            na_y = df_ln[s_pair][i_date:i_date+i_lookback].values
            na_x, na_y = np.atleast_2d(na_x).T, np.atleast_2d(na_y).T
            slope, intercept = lrll.total_least_squares(na_x, na_y)
            na_line = (slope * na_x + intercept)
            na_diff = na_y - na_line
            f_mean = np.mean(na_diff)
            f_std = np.std(na_diff)
            # judge whether events triggered
            if na_diff[-2] < f_mean + f_std and na_diff[-1] >= f_mean + f_std:
                # find holding period
                i_holding_period = 0
                f_residual_yest = 1.0
                f_residual_today = 1.0
                b_flag = True
                while(f_residual_yest * f_residual_today > 0.):
                    i_holding_period += 1
                    if i_holding_period == i_max_holding:
                        b_flag = False
                        break
                    '''
                    # Stop loss
                    i_tmp = i_date + i_lookback + i_holding_period - 1
                    f_rets = df_close[s_sym][i_tmp]/df_open[s_sym][i_date+i_lookback]\
                    - df_close[s_pair][i_tmp]/df_open[s_pair][i_date+i_lookback]
                    if f_rets <= 1 - f_stop_loss:
                        b_flag = False
                        break
                    '''
                    # Standard exit
                    na_x = df_ln[s_sym][i_date+i_holding_period:i_date+\
                    i_lookback+i_holding_period].values
                    na_y = df_ln[s_pair][i_date+i_holding_period:i_date+\
                    i_lookback+i_holding_period].values
                    na_x, na_y = np.atleast_2d(na_x).T, np.atleast_2d(na_y).T
                    slope, intercept = lrll.total_least_squares(na_x, na_y)
                    na_diff_lookforward = na_y - (slope * na_x + intercept)
                    f_mean_lookforward = np.mean(na_diff_lookforward)
                    f_residual_yest = na_diff_lookforward[-2] - f_mean_lookforward
                    f_residual_today = na_diff_lookforward[-1] - f_mean_lookforward
                #if b_flag == False:
                #    continue
                dt_exit = lrlu.get_nyse_offset(dt_date, i_holding_period)
                if dt_exit >= dt_end:
                    dt_exit = dt_end
                t_order = ((s_sym, s_pair), dt_exit, (1.0, -1.0))
                ls_orders.append(t_order)
                df_holding[s_sym] = float(i_holding_period)
                df_holding[s_pair] = float(i_holding_period)
                continue
            elif na_diff[-2] > f_mean - f_std and na_diff[-1] <= f_mean - f_std:
                # find holding period
                i_holding_period = 0
                f_residual_yest = 1.0
                f_residual_today = 1.0
                b_flag = True
                while(f_residual_yest * f_residual_today > 0.):
                    i_holding_period += 1
                    if i_holding_period == i_max_holding:
                        b_flag = False
                        break
                    '''
                    # Stop loss
                    i_tmp = i_date + i_lookback + i_holding_period - 1
                    f_rets = df_close[s_pair][i_tmp]/df_open[s_pair][i_date+i_lookback]\
                    - df_close[s_sym][i_tmp]/df_open[s_sym][i_date+i_lookback]
                    if f_rets <= 1 - f_stop_loss:
                        b_flag = False
                        break
                    '''
                    # Standard exit
                    na_x = df_ln[s_sym][i_date+i_holding_period:i_date+\
                    i_lookback+i_holding_period].values
                    na_y = df_ln[s_pair][i_date+i_holding_period:i_date+\
                    i_lookback+i_holding_period].values
                    na_x, na_y = np.atleast_2d(na_x).T, np.atleast_2d(na_y).T
                    slope, intercept = lrll.total_least_squares(na_x, na_y)
                    na_diff_lookforward = na_y - (slope * na_x + intercept)
                    f_mean_lookforward = np.mean(na_diff_lookforward)
                    f_residual_yest = na_diff_lookforward[-2] - f_mean_lookforward
                    f_residual_today = na_diff_lookforward[-1] - f_mean_lookforward
                #if b_flag == False:
                #    continue
                dt_exit = lrlu.get_nyse_offset(dt_date, i_holding_period)
                if dt_exit >= dt_end:
                    dt_exit = dt_end
                t_order = ((s_pair, s_sym), dt_exit, (1.0, -1.0))
                ls_orders.append(t_order)
                df_holding[s_sym] = float(i_holding_period)
                df_holding[s_pair] = float(i_holding_period)
                continue
        if ls_orders:
            ddt_lt_syms[dt_date] = ls_orders
        df_holding -= 1
        df_holding[df_holding < 0] = 0

    # Backtest
    dt_temp_date = lrlu.get_nyse_offset(dt_end, -1)
    if dt_temp_date not in ddt_lt_syms:
        ddt_lt_syms[dt_temp_date] = []
    ldt_dates = sorted(ddt_lt_syms.keys())
    print "Running Backtest"
    c_strat = lrlbtr.LrlStratConfig(
            f_value=10000000.0,
            s_period=ldt_dates,
            dt_start=dt_start,
            dt_end=dt_end,
            s_name='Pairs Trade Backtest',
            s_display_name='Palo Pairs Trading',
            s_subscriber_email='weiyi.alan.chen@gmail.com',
            i_subscriber_id=754,
            s_description=None,
            s_benchmark='$SPX',
            s_benchmark_name='S&P 500',
            b_sell_on_target=True,
            d_sell_on_target_args={'i_holding_period': None,
                                    'b_event': True},
            d_custom_settings={},

            fc_univ=lrls.univ_basic,
            d_univ_args={'o_white':s_list, 'o_black':[],
                'o_hedge_white':[], 'o_hedge_black':[]},

            fc_scan=lrls.scan_none,
            d_scan_args={},

            fc_prior=lrls.prior_none,
            d_prior_args={},

            fc_alloc=lrls.alloc_event_fft_backtest,
            d_alloc_args={'ddt_lt_syms':ddt_lt_syms,
                        'f_cash_cent':f_cash_cent,
                        'i_max_equities':i_max_equities,
                        'f_core_weight':1.0},

            fc_opt=lrls.optimize_none,
            d_opt_args={},

            fc_hedge=lrls.hedge_none,
            d_hedge_args={},

            fc_sim=lrls.sim_basic,
            d_sim_args={'f_slippage':f_slippage,
                        'f_minimumcommision':f_minimumcommision,
                        'f_commision_share':f_commision_share,
                        'i_target_leverage':i_target_leverage,
                        'f_borrow_rate':f_borrow_rate})
    lrlbtr.backtest(c_strat, b_curl=False, b_plot=True)
    
if __name__ == '__main__':
    trade_lr_pairs()
