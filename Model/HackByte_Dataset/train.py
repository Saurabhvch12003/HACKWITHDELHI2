import argparse
from ultralytics import YOLO
import os

# Default hyperparameters
EPOCHS = 5
MOSAIC = 0.1
OPTIMIZER = 'AdamW'
MOMENTUM = 0.2
LR0 = 0.001
LRF = 0.0001
SINGLE_CLS = False

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--epochs', type=int, default=EPOCHS, help='Number of epochs')
    parser.add_argument('--mosaic', type=float, default=MOSAIC, help='Mosaic augmentation')
    parser.add_argument('--optimizer', type=str, default=OPTIMIZER, help='Optimizer')
    parser.add_argument('--momentum', type=float, default=MOMENTUM, help='Momentum')
    parser.add_argument('--lr0', type=float, default=LR0, help='Initial learning rate')
    parser.add_argument('--lrf', type=float, default=LRF, help='Final learning rate')
    parser.add_argument('--single_cls', type=bool, default=SINGLE_CLS, help='Single class training')
    args = parser.parse_args()

    # Set working directory
    this_dir = os.path.dirname(__file__)
    os.chdir(this_dir)

    # Load YOLO model
    model = YOLO(os.path.join(this_dir, "yolov8s.pt"))

    # Prepare training parameters
    overrides = {
        'data': os.path.join(this_dir, "yolo_params.yaml"),
        'epochs': args.epochs,
        'device': 0,
        'mosaic': args.mosaic,
        'optimizer': args.optimizer,
        'lr0': args.lr0,
        'lrf': args.lrf,
        'momentum': args.momentum,
        'single_cls': args.single_cls,
        # Add built-in augmentations below:
        'hsv_v': 0.3,     # Reduce from 0.5 to 0.3 (less brightness jitter)
        'degrees': 5,     # Reduce from 10 to 5 (smaller rotations)
        'flipud': 0.1,    # Reduce from 0.2 to 0.1 (less vertical flipping)
        'fliplr': 0.3,    # Reduce from 0.5 to 0.3 (less horizontal flipping)
        'erasing': 0.2    # Reduce from 0.4 to 0.2 (less random erasing/occlusion)

        
        # 'hsv_v': 0.5,        # Vary brightness (0.0–1.0)
        # 'degrees': 10,       # Random rotation (+/- degrees)
        # 'flipud': 0.2,       # 20% probability vertical flip
        # 'fliplr': 0.5,       # 50% probability horizontal flip
        # 'erasing': 0.4,      # 40% probability of random erasing/occlusion
    }

    # Train the model
    results = model.train(**overrides)


    # results = model.train(
    #     data=os.path.join(this_dir, "yolo_params.yaml"), 
    #     epochs=args.epochs,
    #     device=0,
    #     single_cls=args.single_cls, 
    #     mosaic=args.mosaic,
    #     optimizer=args.optimizer, 
    #     lr0 = args.lr0, 
    #     lrf = args.lrf, 
    #     momentum=args.momentum
    # )
'''
Mixup boost val pred but reduces test pred
Mosaic shouldn't be 1.0  
'''


'''
                   from  n    params  module                                       arguments
  0                  -1  1       464  ultralytics.nn.modules.conv.Conv             [3, 16, 3, 2]
  1                  -1  1      4672  ultralytics.nn.modules.conv.Conv             [16, 32, 3, 2]
  2                  -1  1      7360  ultralytics.nn.modules.block.C2f             [32, 32, 1, True]
  3                  -1  1     18560  ultralytics.nn.modules.conv.Conv             [32, 64, 3, 2]
  4                  -1  2     49664  ultralytics.nn.modules.block.C2f             [64, 64, 2, True]
  5                  -1  1     73984  ultralytics.nn.modules.conv.Conv             [64, 128, 3, 2]
  6                  -1  2    197632  ultralytics.nn.modules.block.C2f             [128, 128, 2, True]
  7                  -1  1    295424  ultralytics.nn.modules.conv.Conv             [128, 256, 3, 2]
  8                  -1  1    460288  ultralytics.nn.modules.block.C2f             [256, 256, 1, True]
  9                  -1  1    164608  ultralytics.nn.modules.block.SPPF            [256, 256, 5]
 10                  -1  1         0  torch.nn.modules.upsampling.Upsample         [None, 2, 'nearest']
 11             [-1, 6]  1         0  ultralytics.nn.modules.conv.Concat           [1]
 12                  -1  1    148224  ultralytics.nn.modules.block.C2f             [384, 128, 1]
 13                  -1  1         0  torch.nn.modules.upsampling.Upsample         [None, 2, 'nearest']
 14             [-1, 4]  1         0  ultralytics.nn.modules.conv.Concat           [1]
 15                  -1  1     37248  ultralytics.nn.modules.block.C2f             [192, 64, 1]
 16                  -1  1     36992  ultralytics.nn.modules.conv.Conv             [64, 64, 3, 2]
 17            [-1, 12]  1         0  ultralytics.nn.modules.conv.Concat           [1]
 18                  -1  1    123648  ultralytics.nn.modules.block.C2f             [192, 128, 1]
 19                  -1  1    147712  ultralytics.nn.modules.conv.Conv             [128, 128, 3, 2]
 20             [-1, 9]  1         0  ultralytics.nn.modules.conv.Concat           [1]
 21                  -1  1    493056  ultralytics.nn.modules.block.C2f             [384, 256, 1]
 22        [15, 18, 21]  1    751507  ultralytics.nn.modules.head.Detect           [1, [64, 128, 256]]
Model summary: 225 layers, 3,011,043 parameters, 3,011,027 gradients, 8.2 GFLOPs
'''