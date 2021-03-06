import os
from torch.autograd import Variable
import torchvision.models as models
import torch
import torchvision
import torch.nn as nn
import torch.optim as optim
import constants


class CDAE(nn.Module):
	"""convolution denoising autoencoder layer for stacked autoencoders"""
	def __init__(self, input_size, output_size, stride):
		super(CDAE, self).__init__()

		self.forward_part = nn.Sequential(
				nn.Conv2d(input_size, output_size, kernel_size=2, stride=stride, padding=0),
				nn.ReLU(),
			)
		self.backward_part = nn.Sequential(
				nn.ConvTranspose2d(output_size, input_size, kernel_size=2, stride=2, padding=0),
				nn.ReLU()
			)

		nn.criterion = nn.MSELoss()
		self.optimizer = optim.SGD(self.parameters(), lr=0.1)

	def forward(self, x):
		x = x.detach()

		x_noisy = x*(Variable(x.data.new(x.size()).normal_(0, 0.1)) > -.1).type_as(x)
		y = self.forward_part(x_noisy)

		if self.training:
			x_reconstruct = self.backward_part(y)
			loss = self.criterion(x_reconstruct, Variable(x.data, require_grad=False))
			self.optimizer.zero_grad()
			loss.backward()
			self.optimizer.step()

		return y.detach()

# class MyAlexNet_SDAe(nn.Module):
# 	def __init__(self, args):

# class MyAlexNet(nn.Module):
# 	def __init__(self, pretrained=False, num_classes = constants.NUM_LABELS):
# 		super(MyAlexNet, self).__init__()
# 		self.pretrained_model = models.AlexNet(pretrained=pretrained)
# 		self.features = self.pretrained_model.features
# 		self.classifier = nn.Sequential(
#             nn.Dropout(),
#             nn.Linear(256 * 7 * 7, 4096),
#             nn.ReLU(inplace=True),
#             nn.Dropout(),
#             nn.Linear(4096, 4096),
#             nn.ReLU(inplace=True),
#             nn.Linear(4096, num_classes),
#     	)
#     def forward(self, x):
#     	x = self.features(x)
#     	x = x.view(x.size(0), 256 * 7 * 7)
#     	return self.classifier(x)
    
#     def frozen_until(self, to_layer=1):
#     	print('Frozen pretrained model to the first sequential layer')
#     	for child in self.features.children():
#     		for param in child.parameters():
#     			param.require_grad = False

class CustomResnet(nn.Module):
	def __init__(self, depth, num_classes):
		super(CustomResnet, self).__init__()
		if depth == 18:
			self.pretrained_model = models.resnet18(pretrained=True)
		elif depth == 34:
			self.pretrained_model = models.resnet34(pretrained=True)
		elif depth == 50:
			self.pretrained_model = models.resnet50(pretrained=True)
		elif depth == 152:
			self.pretrained_model = models.resnet152(pretrained=True)
		self.num_features = models.fc.in_features

		self.shared = nn.Sequential(*list(self.pretrained_model.children())[:-1])
		self.target = nn.Sequential(nn.Linear(self.num_features, num_classes))
	def forward(self, x):
		x = self.shared(x)
		x = torch.squeeze(x)
		return self.target(x)

	def frozen_until(self, frozen_layer):
		print('Freeze updating weights of network layers to layer {}-th'.format(frozen_layer))
		child_counter = 0
		for child in self.shared.children():
			if child_counter <= frozen_layer:
				print("Child ", child_counter, " was frozen")
				for param in child.parameters():
					param.require_grad = False
			else:
				print("Child ", child_counter, " was not frozen")
				for param in child.parameters():
					param.require_grad = True
			child_counter += 1

def net_frozen(args, model):
	print('----------------------------------------------------------')
	model.frozen_until()
	init_lr = args.lr 
	if args.optim == 'adam':
		optimizer = optim.Adam(filter(lambda p: p.require_grad, model.parameters()), lr=init_lr, weight_decay=args.weight_decay)
	elif args.optim == 'sgd':
		optimizer = optim.SGD(filter(lambda p: p.require_grad, model.parameters()), lr=init_lr, weight_decay=args.weight_decay, momentum=0.9)
	print('----------------------------------------------------------')
	return model, optimizer