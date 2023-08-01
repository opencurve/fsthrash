import torch
import torchvision
import torchvision.transforms as transforms
import os
from torch.utils.data import DataLoader
import sys

max_epochs = int(sys.argv[1])

if not os.path.exists('./intermediate_results'):
    os.makedirs('./intermediate_results')

def save_intermediate_results(outputs, labels, batch_idx):
    for i in range(outputs.shape[0]):
        output = outputs[i]
        label = labels[i]
        filename = f'./intermediate_results/output_{batch_idx}_{i}_{classes[label]}.pt'
        torch.save(output, filename)

# 定义transform
transform = transforms.Compose(
    [transforms.ToTensor(), # 将图像转换为张量
     transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))]) # 对每个通道进行标准化

# 加载训练集和测试集
#trainset = torchvision.datasets.CIFAR10(root='./data', train=True,
#                                        download=True, transform=transform)
#trainloader = torch.utils.data.DataLoader(trainset, batch_size=64,
#                                          shuffle=True, num_workers=2)

#testset = torchvision.datasets.CIFAR10(root='./data', train=False,
#                                       download=True, transform=transform)
#testloader = torch.utils.data.DataLoader(testset, batch_size=4,
#                                         shuffle=False, num_workers=2)

trainset = torchvision.datasets.CIFAR10(root='./data', train=True,
                                        download=True, transform=transform)
testset = torchvision.datasets.CIFAR10(root='./data', train=False,
                                       download=True, transform=transform)

trainloader = DataLoader(trainset, batch_size=64,
                          shuffle=True, num_workers=2)
testloader = DataLoader(testset, batch_size=4,
                         shuffle=False, num_workers=2)


if os.path.exists('./intermediate_results'):
    files = os.listdir('./intermediate_results')
    if len(files) > 0:
        print(f'Found {len(files)} intermediate result files.')
        print('Loading intermediate results...')
        for file in files:
            output = torch.load(f'./intermediate_results/{file}')
            # TODO: 使用 output 进行训练

        # 在加载中间结果时，将之前加载的训练集和测试集数据传递给 DataLoader
        train_loader = DataLoader(trainset, batch_size=64,
                                  shuffle=True, num_workers=2)
        test_loader = DataLoader(testset, batch_size=4,
                                 shuffle=False, num_workers=2)


# 定义类别标签
classes = ('plane', 'car', 'bird', 'cat',
           'deer', 'dog', 'frog', 'horse', 'ship', 'truck')

# 定义神经网络
import torch.nn as nn
import torch.nn.functional as F

class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(3, 6, 5)
        self.pool = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(6, 16, 5)
        self.fc1 = nn.Linear(16 * 5 * 5, 120)
        self.fc2 = nn.Linear(120, 84)
        self.fc3 = nn.Linear(84, 10)

    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = x.view(-1, 16 * 5 * 5)
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        return x

net = Net()

# 定义损失函数和优化器
import torch.optim as optim

criterion = nn.CrossEntropyLoss()
optimizer = optim.SGD(net.parameters(), lr=0.001, momentum=0.9)

num_iterations = len(trainset) // trainloader.batch_size
# 训练网络
for epoch in range(max_epochs):  # 多次循环遍历数据集

    running_loss = 0.0
    for i, data in enumerate(trainloader, 0):
        # 获取输入数据
        inputs, labels = data

        # 梯度置零
        optimizer.zero_grad()

        # 正向传递，反向传递，优化
        outputs = net(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        

        save_intermediate_results(outputs, labels, i)
        # 统计损失值
        running_loss += loss.item()
        if i % 2000 == 1999:    # 每2000个小批量数据打印一次损失值
            print('[%d, %5d] loss: %.3f' %
                  (epoch + 1, i + 1, running_loss / 2000))
            running_loss = 0.0
    torch.save({
    'epoch': epoch,
    'model_state_dict': net.state_dict(),
    'optimizer_state_dict': optimizer.state_dict(),
    'loss': loss
    }, 'checkpoint.pth')

print('Finished Training')

# 测试网络
correct = 0
total = 0
with torch.no_grad():
    for data in testloader:
        images, labels = data
        outputs = net(images)
        _, predicted = torch.max(outputs.data, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()

print('Accuracy of the network on the 10000 test images: %d %%' % (
    100 * correct / total))
