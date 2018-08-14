import os
import copy
import pandas as pd
import numpy as np


class SchduleAlgorithm:
    def __init__(self, inst_path, machine_path, file_machine_resources, file_instance_deploy, file_app_interference, cpu_thresh, save_path):
        self.inst_fea = np.load(inst_path)
        self.machine_fea = np.load(machine_path)
        self.state1 = {}
        self.state2 = {}
        self.app_interfer = {}
        self.inst2app = {}
        self.cpu_thresh = cpu_thresh
        self.machine_file = file_machine_resources
        self.instance_file = file_instance_deploy
        self.interfer_file = file_app_interference
        self.save_path = save_path

    def run(self):
        self.get_inst2app()
        self.get_rule_A_B()
        self.get_machine_stat_init()
        self.findFeasible()
        self.schduling()

    def get_machine_stat_init(self):
        stat_init = {}
        df_machine_resources = pd.read_csv(self.machine_file, header=None, encoding='gbk')
        df_machine_resources.columns = ['machine_id', 'cpu', 'mem', 'disk', 'P', 'M', 'PM']
        df_instance_deploy = pd.read_csv(self.instance_file, header=None, encoding='gbk')
        df_instance_deploy.columns = ['instance_id', 'app_id', 'machine_id']
        for index, row in df_machine_resources.iterrows():
            machine_id = row["machine_id"]
            stat_init[machine_id] = []

        for index, row in df_instance_deploy.iterrows():
            machine_id = row["machine_id"]
            if not pd.isnull(machine_id):
                stat_init[machine_id].append(row["instance_id"])

        self.state1 = stat_init
        for key in self.state1.keys():
            self.state2[key] = []

    def get_inst2app(self):
        df_instance_deploy = pd.read_csv(self.instance_file, header=None, encoding='gbk')
        df_instance_deploy.columns = ['instance_id', 'app_id', 'machine_id']

        for index, row in df_instance_deploy.iterrows():
            self.inst2app[row['instance_id']] = row['app_id']

    def get_rule_A_B(self):
        df_app_interference = pd.read_csv(self.interfer_file, header=None,
                                          encoding='gbk')
        df_app_interference.columns = ['app_id1', 'app_id2', 'k']
        for index, row in df_app_interference.iterrows():
            app_id1 = row["app_id1"]
            app_id2 = row["app_id2"]
            if not app_id2 in self.app_interfer.keys():
                self.app_interfer[app_id2] = {app_id1: row["k"]}
            else:
                self.app_interfer[app_id2][app_id1] = row['k']

    def isAppInterference(self, machine, inst):
        """
        evaluate whether the machine in stat2 is available
        :param machine: machine name
        :param inst: inst name
        """
        in_app = self.inst2app[inst]
        if in_app in self.app_interfer.keys():
            cur_insts = self.state2[machine]
            app_num = {}
            # count app number in current machine
            for inst in cur_insts:
                app = self.inst2app[inst]
                if app not in app_num.keys():
                    app_num[app] = 1
                else:
                    app_num[app] += 1
            mini = 1e9
            for app in self.app_interfer[in_app].keys():
                if app in app_num.keys():
                    if self.app_interfer[in_app][app] < mini:
                        mini = self.app_interfer[in_app][app]
            if in_app not in app_num.keys():
                if mini == 0:
                    return True
            elif app_num[in_app] >= mini:
                return True
        return False

    def findFeasible(self):
        print('Finding feasibel solution ...')
        
        machines_load = np.zeros((self.machine_fea.shape[0], 200))
        from time import time
        count = 0
        begin = time()
        for inst_id in range(self.inst_fea.shape[0]):
            flag = 0
            for machine_id in range(self.machine_fea.shape[0]):
                machine_load = machines_load[machine_id]
                after_load = machine_load + self.inst_fea[inst_id, 1:]
                
                cpu = np.max(after_load[:98]/self.machine_fea[machine_id, 1:99])
                mem = np.max(after_load[98:196]/self.machine_fea[machine_id, 99:197])
                others = np.max(after_load[196:]/self.machine_fea[machine_id, 197:])
                machine_str_id = "machine_" + str(int(self.machine_fea[machine_id, 0]))
                inst_str_id = "inst_" + str(int(self.inst_fea[inst_id, 0]))
                if mem>1 or others>1 or cpu>self.cpu_thresh or self.isAppInterference(machine_str_id, inst_str_id):
                    pass
                else:
                    machines_load[machine_id] = after_load
                    flag = 1

                    self.state2[machine_str_id].append(inst_str_id)

                    count += 1
                    if count% 10000 == 0 :
                        print("count %d: time: %d"%(count, time()-begin))

                    break
                    
            if not flag:
                raise RuntimeError('No available machine for current inst!')

    def schduling(self):
        print('Geting schduling results ... ')
        save_path = self.save_path
        with open(save_path, 'w') as fout:
            machines = self.machine_fea[:, 0]
            for i in range(machines.shape[0]):
                machine = 'machine_'+(str(int(machines[i])))
                ori_state = self.state1[machine]
                cur_state = self.state2[machine]
                print('origin state: ', ori_state)
                print('current state: ', cur_state)
                out_inst = list(set(ori_state)-set(cur_state))
                print('out inst: ', out_inst)
                in_inst = list(set(cur_state)-set(ori_state))
                print('in inst', in_inst)
                for inst in out_inst:
                    flag = 0
                    for j in range(i+1, len(machines)):
                        if self.isMachineAvailable(machines[j], inst, 1):
                            out_machine = 'machine_'+str(machines[j])
                            self.state2[out_machine].append(inst)
                            self.state2[machine].pop(self.state2[machine].index(inst))
                            fout.write('{}, {}'.format(inst, out_machine))
                            flag = 1
                            break
                        else:
                            pass
                    if not flag:
                        raise RuntimeError('No available machine for current inst!')
                for inst in in_inst:
                    flag = 0
                    for j in range(i+1, len(machines)):
                        out_machine = 'machine_' + str(machines[j])
                        if inst in self.state2[out_machine]:
                            self.state2[machine].append(inst)
                            self.state2[out_machine].pop(self.state2[out_machine].index(inst))
                            fout.write('{}, {}'.format(inst, machine))
                            flag = 1
                            break

                    if not flag:
                        raise RuntimeError('No available machine for current inst!')


if __name__ == '__main__':
    inst_path = './data/instances.npy'
    machine_path = './data/machines.npy'
    file_machine_resources = './data/scheduling_preliminary_a_machine_resources_20180606.csv'
    file_instance_deploy = './data/scheduling_preliminary_a_instance_deploy_20180606.csv'
    file_app_interference = './data/scheduling_preliminary_a_app_interference_20180606.csv'
    save_path = './data/submit_team_05_hhmmss.txt'

    cpu_thresh = 0.5
    run_schdule = SchduleAlgorithm(inst_path, machine_path, file_machine_resources, file_instance_deploy, file_app_interference, cpu_thresh, save_path)
    run_schdule.run()
