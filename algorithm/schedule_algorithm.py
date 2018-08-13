import os
import copy
import pandas as pd
import numpy as np


class SchduleAlgorithm:
    def __init__(self, inst_path, machine_path, file_machine_resources, file_instance_deploy, cpu_thresh):
        self.inst_fea = np.load(inst_path)
        self.machine_fea = np.load(machine_path)
        self.state1 = {}
        self.state2 = {}
        self.cpu_thresh = cpu_thresh
        self.machine_file = file_machine_resources
        self.instance_file = file_instance_deploy

    def run(self):
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

    def isMachineAvailable(self, machine, inst):
        """
        evaluate whether the machine in stat2 is available
        :param machine: machine name
        :param inst: inst name
        """
        inst_id = np.argwhere(self.inst_fea[:, 0] == int(inst[5:]))

        all_inst = self.inst_fea[inst_id, 1:]
        for i in self.state2[machine]:
            i = int(i[5:])
            index = np.argwhere(self.inst_fea[:, 0] == i)
            all_inst += self.inst_fea[index, 1:]
        # print(all_inst[0, 0, :98].shape, self.machine_fea[0,:].shape)
        machine_id = np.argwhere(self.machine_fea[:, 0] == int(machine[8:]))
        cpu = np.max(all_inst[0, 0, :98]/self.machine_fea[machine_id, 1:99])
        mem = np.max(all_inst[0, 0, 98:196]/self.machine_fea[machine_id, 99:197])
        others = np.max(all_inst[0, 0, 196:]/self.machine_fea[machine_id, 197:])
        if mem > 1 or others > 1 or cpu > self.cpu_thresh:
            return False
        return True

    def findFeasible(self):
        print('Finding feasibel solution ...')
        insts = self.inst_fea[:, 0]
        for i in range(insts.shape[0]):
            inst = 'inst_'+(str(int(insts[i])))
            flag = 0
            for machine in self.state2:
                if self.isMachineAvailable(machine, inst):
                    self.state2[machine].append(inst)
                    flag = 1
                else:
                    pass
            if not flag:
                raise RuntimeError('No available machine for current inst!')

    def schduling(self):
        print('Geting schduling results ... ')
        machines = self.machine_fea[:, 0]
        for i in range(machines.shape[0]):
            machine = 'machine_'+(str(int(machines[i])))
            ori_state = self.state1[machine]
            cur_state = self.state2[machine]
            print('origin state: ', ori_state)
            print('current state: ', cur_state)
            out_inst = list(set(ori_state)^set(cur_state))
            print('out inst: ', out_inst)
            in_inst = list(set(ori_state)^set(cur_state))
            print('in inst', in_inst)
            for inst in out_inst:
                flag = 0
                for j in range(i+1, len(machines)):
                    if self.isMachineAvailable(machines[j], inst):
                        self.state2[machines[j]].append(inst)
                        flag = 1
                    else:
                        pass
                if not flag:
                    raise RuntimeError('No available machine for current inst!')
            for inst in in_inst:
                self.state2[machines[i]].append(inst)

            # TODO: Need to evaluate whether the machine state is legal


if __name__ == '__main__':
    inst_path = './data/instances.npy'
    machine_path = './data/machines.npy'
    file_machine_resources = './data/scheduling_preliminary_a_machine_resources_20180606.csv'
    file_instance_deploy = './data/scheduling_preliminary_a_instance_deploy_20180606.csv'
    cpu_thresh = 0.5
    run_schdule = SchduleAlgorithm(inst_path, machine_path, file_machine_resources, file_instance_deploy, cpu_thresh)
    run_schdule.run()