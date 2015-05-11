
# Python imports
import time
import datetime as dt

# 3rd party imports
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# LRL imports
import lrlsql as lrlsq
import lrlutil as lrlu
import lrllearn as lrll


def select_lr_pairs():
    # Parameter to manipulate
    dt_start = dt.datetime(2009, 1, 1, 16)
    dt_end = dt.datetime(2009, 12, 31, 16)
    s_list = 'S&P 500'
    i_lookback = 252
    f_min_corr = 0.99
    f_cross_rank = 0.2

    # Access data
    ls_syms = lrlsq.lsq_list(s_list)
    ls_keys = ['close']
    dt_data_start = lrlu.get_nyse_offset(dt_start, -i_lookback+1)
    ldfData = lrlsq.lsq_data(dt_data_start, dt_end, ls_syms, ls_keys)
    d_data = dict(zip(ls_keys, ldfData))
    df_close = d_data['close']
    df_ln = np.log(df_close)
    
    # Select pairs
    for i_date, dt_date in enumerate(df_ln.index[i_lookback:]):
        # read df_pairs from pairs.pkl
        s_filename = 'pairs' + str(hash(dt_date)) + '.pkl' 
        df_pairs = lrlu.cache_get(s_filename)
        # select pairs by correlation
        df_pairs = df_pairs[df_pairs['corr'] > f_min_corr]
        # select pairs by crossing rank
        df_pairs = df_pairs.sort(['cross'])
        df_pairs['cross_rank'] = 0.0
        for i_tmp, i_pairs in enumerate(df_pairs.index):
            df_pairs['cross_rank'][i_pairs] = float(i_tmp)/len(df_pairs.index)
        df_pairs = df_pairs[df_pairs['cross_rank'] <= f_cross_rank]


        # Learn and validation
        '''
        df_pairs['validation'] = 0.0
        for i_sym_pair in range(len(df_pairs.index)):
            s_sym_pair = df_pairs.index[i_sym_pair]
            s_sym, s_pair = s_sym_pair.split(',')
            i_lookback_learn = i_lookback * 9 / 12
            na_x = df_ln[s_sym][i_date - i_lookback + 1: i_date - i_lookback + \
            i_lookback_learn + 1].values
            na_y = df_ln[s_pair][i_date - i_lookback + 1: i_date - i_lookback +\
            i_lookback_learn + 1].values
            na_x, na_y = np.atleast_2d(na_x).T, np.atleast_2d(na_y).T
            slope, intercept = lrll.total_least_squares(na_x, na_y)         
            na_x = df_ln[s_sym][i_date - i_lookback + i_lookback_learn + 1: \
            i_date + 1].values
            na_y = df_ln[s_pair][i_date - i_lookback + i_lookback_learn + 1: \
            i_date + 1].values
            na_line = (slope * na_x + intercept)
            na_diff = na_y - na_line
            f_mean, f_std = np.mean(na_diff), np.std(na_diff)
            df_pairs['validation'][i_sym_pair] = abs(f_mean / f_std)

        df_pairs = df_pairs.sort(['validation'])
        df_pairs['validation_rank'] = 0.0
        i_len_pairs = df_pairs.shape[0]
        for i_sym_pair in range(i_len_pairs):
            df_pairs['validation_rank'][i_sym_pair] = i_sym_pair/float(\
                i_len_pairs)
        df_pairs = df_pairs[df_pairs['validation_rank'] <= 0.5]
        '''
        # save pairs to selected.pkl
        s_filename = 'selected' + str(hash(dt_date)) + '.pkl'
        print dt_date, len(df_pairs.index)
        lrlu.cache_set(df_pairs, s_filename)


if __name__ == '__main__':
    select_lr_pairs()
