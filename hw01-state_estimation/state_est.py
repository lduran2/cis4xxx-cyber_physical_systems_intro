r'''
 Canonical : https://github.com/lduran2/cis4xxx-cyber_physical_systems_intro/blob/master/hw01-state_estimation/state_est.py
 Simulates the state emulation process in a power grid.
 By        : Leomar Durán <https://github.com/lduran2>
 When      : 2022-02-14t23:02R
 For       : CIS 4XXX/Introduction to Cyber-Physical Systems
 Version   : 1.0.1

 CHANGELOG :
    v1.0.1 - 2022-02-14t23:02R <https://github.com/lduran2>
        `get_net` accepts types of networks `net_type`

    v1.0.0 - 2022-02-14t22:49R <https://github.com/lduran2>
        moved simultion to main method

    v0.0.0 - 2022-01-26 <https://www.kkant.net/>
        initial version
 '''

import logging
logging.basicConfig(filename='state_est.log', encoding='utf-8', level=logging.DEBUG)
from pandapower.estimation import estimate
from pandapower.estimation import remove_bad_data
from pandapower.estimation import chi2_analysis
from pandapower.diagnostic import diagnostic
from pandapower.networks import *
from math import fabs
import pandapower as pp

def main():
    net = get_net()
    pp.runpp(net, calculate_voltage_angles=True, enforce_q_lims=False)

    net2 = get_net()

    v_stddev = 0.025 # pu
    pq_stddev = 0.025 # MW/Mvar
    i_stddev= 0.002 # kA

    pass_meases_feedback(net, net2, v_stddev, pq_stddev, i_stddev)
    #diagnostic(net2, report_style='detailed')
    chi2_test = chi2_analysis(net2)
    if chi2_test: 
        print("Bad data found")
        success = remove_bad_data(net2)
    else:     
        success = False
    #success = estimate(net2, calculate_voltage_angles=True, zero_injection='auto', init='flat')
    if success:
        V, delta = net2.res_bus_est.vm_pu, net2.res_bus_est.va_degree
        print("Voltages: ")
        print(V, sep=' ')
        print("\n Voltage angles: ", delta, sep=' ')
        print_est_comparison(net, net2, 1, 0.001)
# end def main()

#################################################################################################################################

def get_net(net_type=case9):
    print(fr"===running {net_type} net===")
    return net_type()

def print_net_est_res(net):

    print("\n########################################################################################################")

    print(">>> est_res_bus:")
    print(net.res_bus_est[['vm_pu', 'p_mw', 'q_mvar']])
    print(">>> est_res_trafo:")
    print(net.res_trafo_est[['p_hv_mw', 'q_hv_mvar', 'p_lv_mw', 'q_lv_mvar', 'i_hv_ka', 'i_lv_ka']])
    print(">>> est_res_trafo3w:")
    print(net.res_trafo3w_est[['p_hv_mw', 'q_hv_mvar', 'p_mv_mw', 'q_mv_mvar', 'p_lv_mw', 'q_lv_mvar', 'i_hv_ka', 'i_mv_ka', 'i_lv_ka']])
    print(">>> est_res_line:")
    print(net.res_line_est[['p_from_mw', 'q_from_mvar', 'p_to_mw', 'q_to_mvar', 'i_from_ka', 'i_to_ka']])

def print_est_comparison(net, net2, alarm_thr, noise_lim):
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)

    def diff_stat(ref_val, val, alarm_thr, noise_lim):
        try:
            abs_diff = ref_val - val
        except Exception as ex:
            print(ex)

        if fabs(ref_val) < noise_lim or fabs(val) < noise_lim:
            return '+'
        else:
            rel_diff = fabs(100 * abs_diff / ref_val)
            if rel_diff > alarm_thr:
                return '{:.3e}({:.2f}%)'.format(abs_diff, rel_diff)
            else:
                return '+'

    # bus`s
    for busIndex in net.bus.index:
        net2.res_bus_est.vm_pu[busIndex] = diff_stat(net.res_bus.vm_pu[busIndex], net2.res_bus_est.vm_pu[busIndex], alarm_thr, noise_lim)
        net2.res_bus_est.p_mw[busIndex] = diff_stat(net.res_bus.p_mw[busIndex], net2.res_bus_est.p_mw[busIndex], alarm_thr, noise_lim)
        net2.res_bus_est.q_mvar[busIndex] = diff_stat(net.res_bus.q_mvar[busIndex], net2.res_bus_est.q_mvar[busIndex], alarm_thr, noise_lim)

    # line`s
    for lineIndex in net.line.index:
        net2.res_line_est.p_from_mw[lineIndex] = diff_stat(net.res_line.p_from_mw[lineIndex], net2.res_line_est.p_from_mw[lineIndex], alarm_thr, noise_lim)
        net2.res_line_est.p_to_mw[lineIndex] = diff_stat(net.res_line.p_to_mw[lineIndex], net2.res_line_est.p_to_mw[lineIndex], alarm_thr, noise_lim)

        net2.res_line_est.q_from_mvar[lineIndex] = diff_stat(net.res_line.q_from_mvar[lineIndex], net2.res_line_est.q_from_mvar[lineIndex], alarm_thr, noise_lim)
        net2.res_line_est.q_to_mvar[lineIndex] = diff_stat(net.res_line.q_to_mvar[lineIndex], net2.res_line_est.q_to_mvar[lineIndex], alarm_thr, noise_lim)

        net2.res_line_est.i_from_ka[lineIndex] = diff_stat(net.res_line.i_from_ka[lineIndex], net2.res_line_est.i_from_ka[lineIndex], alarm_thr, noise_lim)
        net2.res_line_est.i_to_ka[lineIndex] = diff_stat(net.res_line.i_to_ka[lineIndex], net2.res_line_est.i_to_ka[lineIndex], alarm_thr, noise_lim)

    # trafo`s
    for trafoIndex in net.trafo.index:
        net2.res_trafo_est.p_hv_mw[trafoIndex] = diff_stat(net.res_trafo.p_hv_mw[trafoIndex], net2.res_trafo_est.p_hv_mw[trafoIndex], alarm_thr, noise_lim)
        net2.res_trafo_est.p_lv_mw[trafoIndex] = diff_stat(net.res_trafo.p_lv_mw[trafoIndex], net2.res_trafo_est.p_lv_mw[trafoIndex], alarm_thr, noise_lim)

        net2.res_trafo_est.q_hv_mvar[trafoIndex] = diff_stat(net.res_trafo.q_hv_mvar[trafoIndex], net2.res_trafo_est.q_hv_mvar[trafoIndex], alarm_thr, noise_lim)
        net2.res_trafo_est.q_lv_mvar[trafoIndex] = diff_stat(net.res_trafo.q_lv_mvar[trafoIndex], net2.res_trafo_est.q_lv_mvar[trafoIndex], alarm_thr, noise_lim)

        net2.res_trafo_est.i_hv_ka[trafoIndex] = diff_stat(net.res_trafo.i_hv_ka[trafoIndex], net2.res_trafo_est.i_hv_ka[trafoIndex], alarm_thr, noise_lim)
        net2.res_trafo_est.i_lv_ka[trafoIndex] = diff_stat(net.res_trafo.i_lv_ka[trafoIndex], net2.res_trafo_est.i_lv_ka[trafoIndex], alarm_thr, noise_lim)

    # trafo3w`s
    for trafoIndex in net.trafo3w.index:
        net2.res_trafo3w_est.p_hv_mw[trafoIndex] = diff_stat(net.res_trafo3w.p_hv_mw[trafoIndex], net2.res_trafo3w_est.p_hv_mw[trafoIndex], alarm_thr, noise_lim)
        net2.res_trafo3w_est.p_lv_mw[trafoIndex] = diff_stat(net.res_trafo3w.p_lv_mw[trafoIndex], net2.res_trafo3w_est.p_lv_mw[trafoIndex], alarm_thr, noise_lim)
        net2.res_trafo3w_est.p_mv_mw[trafoIndex] = diff_stat(net.res_trafo3w.p_mv_mw[trafoIndex], net2.res_trafo3w_est.p_mv_mw[trafoIndex], alarm_thr, noise_lim)

        net2.res_trafo3w_est.q_hv_mvar[trafoIndex] = diff_stat(net.res_trafo3w.q_hv_mvar[trafoIndex], net2.res_trafo3w_est.q_hv_mvar[trafoIndex], alarm_thr, noise_lim)
        net2.res_trafo3w_est.q_lv_mvar[trafoIndex] = diff_stat(net.res_trafo3w.q_lv_mvar[trafoIndex], net2.res_trafo3w_est.q_lv_mvar[trafoIndex], alarm_thr, noise_lim)
        net2.res_trafo3w_est.q_mv_mvar[trafoIndex] = diff_stat(net.res_trafo3w.q_mv_mvar[trafoIndex], net2.res_trafo3w_est.q_mv_mvar[trafoIndex], alarm_thr, noise_lim)

        net2.res_trafo3w_est.i_hv_ka[trafoIndex] = diff_stat(net.res_trafo3w.i_hv_ka[trafoIndex], net2.res_trafo3w_est.i_hv_ka[trafoIndex], alarm_thr, noise_lim)
        net2.res_trafo3w_est.i_lv_ka[trafoIndex] = diff_stat(net.res_trafo3w.i_lv_ka[trafoIndex], net2.res_trafo3w_est.i_lv_ka[trafoIndex], alarm_thr, noise_lim)
        net2.res_trafo3w_est.i_mv_ka[trafoIndex] = diff_stat(net.res_trafo3w.i_mv_ka[trafoIndex], net2.res_trafo3w_est.i_mv_ka[trafoIndex], alarm_thr, noise_lim)

    print_net_est_res(net2)

def pass_meases_feedback(net, net2, v_stddev, pq_stddev, i_stddev):
    # bus`s
    for busIndex in net.bus.index:
        vn_pu = net.res_bus.vm_pu[busIndex]
        if busIndex == 5:
            x=0.20
        else:
            x=0
        pp.create_measurement(net2, "v", "bus", vn_pu+x, v_stddev, element=busIndex)

        p_mw = net.res_bus.p_mw[busIndex]
        if p_mw != 0:
            pp.create_measurement(net2, "p", "bus", p_mw, pq_stddev, element=busIndex)
        q_mvar = net.res_bus.q_mvar[busIndex]
        if q_mvar != 0:
            pp.create_measurement(net2, "q", "bus", q_mvar, pq_stddev, element=busIndex)

    # line`s
    for lineIndex in net.line.index:
        p_from_mw = net.res_line.p_from_mw[lineIndex]
        pp.create_measurement(net2, "p", "line", p_from_mw, pq_stddev, element=lineIndex, side="from")
        p_to_mw = net.res_line.p_to_mw[lineIndex]
        pp.create_measurement(net2, "p", "line", p_to_mw, pq_stddev, element=lineIndex, side="to")

        q_from_mvar = net.res_line.q_from_mvar[lineIndex]
        pp.create_measurement(net2, "q", "line", q_from_mvar, pq_stddev, element=lineIndex, side="from")
        q_to_mvar = net.res_line.q_to_mvar[lineIndex]
        pp.create_measurement(net2, "q", "line", q_to_mvar, pq_stddev, element=lineIndex, side="to")

        # i_from_ka = net.res_line.i_from_ka[lineIndex]
        # pp.create_measurement(net2, "i", "line", i_from_ka, i_stddev, element=lineIndex, side="from")
        # i_to_ka = net.res_line.i_to_ka[lineIndex]
        # pp.create_measurement(net2, "i", "line", i_to_ka, i_stddev, element=lineIndex, side="to")

    # trafo`s
    for trafoIndex in net.trafo.index:
        p_hv_mw = net.res_trafo.p_hv_mw[trafoIndex]
        pp.create_measurement(net2, "p", "trafo", p_hv_mw, pq_stddev, element=trafoIndex, side="hv")
        p_lv_mw = net.res_trafo.p_lv_mw[trafoIndex]
        pp.create_measurement(net2, "p", "trafo", p_lv_mw, pq_stddev, element=trafoIndex, side="lv")

        q_hv_mvar = net.res_trafo.q_hv_mvar[trafoIndex]
        pp.create_measurement(net2, "q", "trafo", q_hv_mvar, pq_stddev, element=trafoIndex, side="hv")
        q_lv_mvar = net.res_trafo.q_lv_mvar[trafoIndex]
        pp.create_measurement(net2, "q", "trafo", q_lv_mvar, pq_stddev, element=trafoIndex, side="lv")

        # i_hv_ka = net.res_trafo.i_hv_ka[trafoIndex]
        # pp.create_measurement(net2, "i", "trafo", i_hv_ka, i_stddev, element=trafoIndex, side="hv")
        # i_lv_ka = net.res_trafo.i_lv_ka[trafoIndex]
        # pp.create_measurement(net2, "i", "trafo", i_lv_ka, i_stddev, element=trafoIndex, side="lv")

    # trafo3w`s
    for trafoIndex in net.trafo3w.index:

        p_hv_mw = net.res_trafo3w.p_hv_mw[trafoIndex]
        pp.create_measurement(net2, "p", "trafo3w", p_hv_mw, pq_stddev, element=trafoIndex, side="hv")
        p_lv_mw = net.res_trafo3w.p_lv_mw[trafoIndex]
        pp.create_measurement(net2, "p", "trafo3w", p_lv_mw, pq_stddev, element=trafoIndex, side="lv")
        p_mv_mw = net.res_trafo3w.p_mv_mw[trafoIndex]
        pp.create_measurement(net2, "p", "trafo3w", p_mv_mw, pq_stddev, element=trafoIndex, side="mv")

        q_hv_mvar = net.res_trafo3w.q_hv_mvar[trafoIndex]
        pp.create_measurement(net2, "q", "trafo3w", q_hv_mvar, pq_stddev, element=trafoIndex, side="hv")
        q_lv_mvar = net.res_trafo3w.q_lv_mvar[trafoIndex]
        pp.create_measurement(net2, "q", "trafo3w", q_lv_mvar, pq_stddev, element=trafoIndex, side="lv")
        q_mv_mvar = net.res_trafo3w.q_mv_mvar[trafoIndex]
        pp.create_measurement(net2, "q", "trafo3w", q_mv_mvar, pq_stddev, element=trafoIndex, side="mv")

        # i_hv_ka = net.res_trafo3w.i_hv_ka[trafoIndex]
        # pp.create_measurement(net2, "i", "trafo3w", i_hv_ka, i_stddev, element=trafoIndex, side="hv")
        # i_lv_ka = net.res_trafo3w.i_lv_ka[trafoIndex]
        # pp.create_measurement(net2, "i", "trafo3w", i_lv_ka, i_stddev, element=trafoIndex, side="lv")
        # i_mv_ka = net.res_trafo3w.i_mv_ka[trafoIndex]
        # pp.create_measurement(net2, "i", "trafo3w", i_mv_ka, i_stddev, element=trafoIndex, side="mv")

#################################################################################################################################

if (__name__==r'__main__'):
    main()
