import random
import torch
import numpy as np
from collections import namedtuple

# Taken and adapted from
# https://github.com/pytorch/tutorials/blob/master/Reinforcement%20(Q-)Learning%20with%20PyTorch.ipynb

Transition = namedtuple(
    'Transition', ('state', 'action', 'reward', 'next_state', 'done'))


class ReplayMemory(object):

    def __init__(self, capacity, device):
        self.device = device
        self.capacity = capacity
        self.memory = []
        self.position = 0

    def add(self, *args):
        """Saves a transition."""
        if len(self.memory) < self.capacity:
            self.memory.append(None)

        reshaped_args = []
        for arg in args:
            reshaped_args.append(np.reshape(arg, (1, -1)))

        self.memory[self.position] = Transition(*reshaped_args)
        self.position = (self.position + 1) % self.capacity

    def add_content_of(self, other):
        """
        Adds the content of another replay buffer to this replay buffer
        :param other: another replay buffer
        """
        latest_trans = other.get_latest(self.capacity)
        for transition in latest_trans:
            self.add(*transition)

    def get_latest(self, latest):
        """
        Returns the latest element from the other buffer with the most recent ones at the end of the returned list
        :param other: another replay buffer
        :param latest: the number of latest elements to return
        :return: a list with the latest elements
        """
        if self.capacity < latest:
            latest_trans = self.memory[self.position:].copy() + self.memory[:self.position].copy()
        elif len(self.memory) < self.capacity:
            latest_trans = self.memory[-latest:].copy()
        elif self.position >= latest:
            latest_trans = self.memory[:self.position][-latest:].copy()
        else:
            latest_trans = self.memory[-latest+self.position:].copy() + self.memory[:self.position].copy()
        return latest_trans

    def add_latest_from(self, other, latest):
        """
        Adds the latest samples from the other buffer to this buffer
        :param other: another replay buffer
        :param latest: the number of elements to add
        """
        latest_trans = other.get_latest(latest)
        for transition in latest_trans:
            self.add(*transition)

    def shuffle(self):
        random.shuffle(self.memory)

    def sample(self, batch_size):
        transitions = random.sample(self.memory, batch_size)
        batch = Transition(*zip(*transitions))

        state = torch.FloatTensor(np.concatenate(batch.state)).to(self.device)
        action = torch.FloatTensor(np.concatenate(batch.action)).to(self.device)
        next_state = torch.FloatTensor(np.concatenate(batch.next_state)).to(self.device)
        reward = torch.FloatTensor(np.concatenate(batch.reward)).to(self.device)
        done = torch.FloatTensor(np.concatenate(batch.done)).to(self.device)
        return state, action, reward, next_state, done

    def sample_from_latest(self, batch_size, latest):
        latest_trans = self.get_latest(latest)
        transitions = random.sample(latest_trans, batch_size)
        batch = Transition(*zip(*transitions))

        state = torch.FloatTensor(np.concatenate(batch.state)).to(self.device)
        action = torch.FloatTensor(np.concatenate(batch.action)).to(self.device)
        next_state = torch.FloatTensor(np.concatenate(batch.next_state)).to(self.device)
        reward = torch.FloatTensor(np.concatenate(batch.reward)).to(self.device)
        done = torch.FloatTensor(np.concatenate(batch.done)).to(self.device)
        return state, action, reward, next_state, done

    def __len__(self):
        return len(self.memory)

    def reset(self):
        self.memory = []
        self.position = 0

    def save_info(self, file_path):
        with open(file_path, "wb") as f:
            np.save(f, np.array([len(self.memory), self.position]))
            for trans in self.memory:
                np.save(f, trans.state)
                np.save(f, trans.action)
                np.save(f, trans.reward)
                np.save(f, trans.next_state)
                np.save(f, trans.done)
    
    def load_info(self, file_path):
        self.memory = []
        with open(file_path, "rb") as f:
            info = np.load(f)
            length, pos = info[0], info[1]
            for _ in range(length):
                s = np.load(f)
                a = np.load(f)
                r = np.load(f)
                ns = np.load(f)
                d = np.load(f)
                t = (s, a, r, ns, d)
                self.add(*t)
            self.position = pos

