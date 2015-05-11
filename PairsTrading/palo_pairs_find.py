
# Python imports
import time
import datetime as dt

# 3rd party imports
from scipy import stats
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# LRL imports
import lrlsql as lrlsq
import lrlutil as lrlu
import lrllearn as lrll
import lrlfeatures as lrlf


def find_lr_pairs(dt_start, dt_end, i_lookback, i_num_best):
    # Parameter to manipulate  
    s_list = 'S&P 500'
    f_min_corr = 0.90
    s_benchmark = '$SPX'

    # Access data
    ls_syms = lrlsq.lsq_list(s_list)
    ls_syms.append(s_benchmark)
    ls_keys = ['close']
    dt_data_start = lrlu.get_nyse_offset(dt_start, -i_lookback+1)
    ldfData = lrlsq.lsq_data(dt_data_start, dt_end, ls_syms, ls_keys)

    # Prepare data
    d_data = dict(zip(ls_keys, ldfData))
    df_beta = lrlf.feat_beta(d_data, lLookback=i_lookback, sMarket='$SPX')
    df_alpha = lrlf.feat_alpha(d_data, i_lookback=i_lookback, s_market='$SPX')
    df_close = d_data['close'].drop(['$SPX'], axis=1)
    df_ln = np.log(df_close).dropna(how='all')
    
    # Find pairs for every day
    for i_date, dt_date in enumerate(df_ln.index[i_lookback:]):
        # save pairs with high correlatin in pkl
        ls_pairs = []
        ls_pairs_weight = []
        ls_pairs_corr = []
        ls_pairs_cross = []
        for i_sym, s_sym in enumerate(df_ln.columns):
            # Get data of X
            na_x = df_ln[s_sym][i_date:i_date+i_lookback].values
            f_valid_value = np.sum(~np.isnan(na_x), axis=0) / float(len(na_x))
            if f_valid_value < 0.8:
                continue
            na_x = np.atleast_2d(na_x).T
            for i_pair, s_pair in enumerate(df_ln.columns[i_sym+1:]):
                print dt_date, s_sym, s_pair
                # Get data of Y
                na_y = df_ln[s_pair][i_date:i_date+i_lookback].values
                f_valid_value = np.sum(~np.isnan(na_y), axis=0) / float(len(na_y))
                if f_valid_value < 0.8:
                    continue
                na_y = np.atleast_2d(na_y).T
                # Calculate correlation and ODR
                r_value, p_value = stats.pearsonr(na_x, na_y)
                if (r_value < f_min_corr) or np.isnan(r_value):
                    continue
                slope, intercept = lrll.total_least_squares(na_x, na_y)
                # Calculate residual spread and cross
                na_diff = na_y - (slope * na_x + intercept)
                i_cross = 0
                for i_tmp, f_residual in enumerate(na_diff):
                    if f_residual * na_diff[i_tmp-1] <= 0:
                        i_cross += 1
                if i_cross == 0:
                    continue
                f_avg_cross = float(i_lookback) / float(i_cross)
                # Calculate weights
                f_sym_beta = df_beta[s_sym][i_lookback+i_date]
                f_pair_beta = df_beta[s_pair][i_lookback+i_date]
                f_sym_weight = f_pair_beta / (f_sym_beta + f_pair_beta)
                f_pair_weight = 1 - f_sym_weight

                # Save information in list for pkl
                ls_pairs.append((s_sym, s_pair))
                ls_pairs_weight.append((f_sym_weight, -f_pair_weight))
                ls_pairs_corr.append(float(r_value))
                ls_pairs_cross.append(f_avg_cross)
        # Save df_pairs to pkl
        if ls_pairs:
            d_pairs = {
            'pairs': pd.Series(ls_pairs), 
            'weight':pd.Series(ls_pairs_weight), 
            'corr': pd.Series(ls_pairs_corr),
            'cross': pd.Series(ls_pairs_cross)
            }
            df_pairs = pd.DataFrame(d_pairs)
            print dt_date, len(df_pairs.index)
            #df_pairs = df_pairs.sort('corr')[::-1][:i_num_best]
            s_filename = 'pairs' + str(hash(dt_date)) + '.pkl'
            lrlu.cache_set(df_pairs, s_filename)


if __name__ == '__main__':
    dt_start = dt.datetime(2009, 1, 1, 16)
    dt_end = dt.datetime(2013, 11, 30, 16)
    i_lookback = 252
    i_num_best = 1000
    find_lr_pairs(dt_start, dt_end, i_lookback, i_num_best)
