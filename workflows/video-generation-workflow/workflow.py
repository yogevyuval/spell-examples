import argparse


parser = argparse.ArgumentParser()
parser.add_argument("--frames", type=int, default=2000, help="Number of frames to be generated")
parser.add_argument("--max_epoch", type=int, default=20, help="max number of epochs")
parser.add_argument("--video", required=True, help="path of the video for training")
parser.add_argument("--train_ratio", type=float, default=0.9, help="ratio of training dataset")
parser.add_argument("--batch_size", type=int, default=16, help="batch size for training")
args = parser.parse_args()

import spell.client
client = spell.client.from_environment()

framenum = args.frames 
max_epochs = args.max_epoch
video_path = args.video
train_ratio = args.train_ratio
batch_size = args.batch_size

# Video to pictures
r = client.runs.new(
    command="python video2pic.py --video {} ".format(video_path) +
            "--train_ratio {}".format(train_ratio),
    commit_label="video-gen",
    idempotent=True
)
print("waiting for run {} to complete".format(r.id))
r.wait_status(client.runs.COMPLETE)
dataset_runid = r.id

# Train
r = client.runs.new(
    command="python pix2pix.py " +
            "--mode train " + 
            "--output_dir model_param " + 
            "--max_epochs {} ".format(max_epochs) +
            "--input_dir data/train " +
            "--which_direction AtoB " +
            "--batch_size {} ".format(batch_size),
    machine_type="V100",
    attached_resources={
        "runs/{}/data".format(dataset_runid): "data"
    },
    commit_label="video-gen",
    idempotent=True
)
print("waiting for run {} to complete".format(r.id))
r.wait_status(client.runs.COMPLETE)
train_runid = r.id

# Test
r = client.runs.new(
    command="bash gen.sh {}".format(framenum),
    machine_type="K80",
    attached_resources={
        "runs/{}/data".format(dataset_runid): "data",
        "runs/{}/model_param".format(train_runid): "model_param"
    },
    commit_label="video-gen",
    idempotent=True
)
print("waiting for run {} to complete".format(r.id))
r.wait_status(client.runs.COMPLETE)
gen_runid = r.id

# Generate video
r = client.runs.new(
    command="python pic2video.py " +
            "--frames {} ".format(framenum),
    attached_resources={
        "runs/{}/data/gen".format(gen_runid): "data/gen"
    },
    commit_label="video-gen"
)
print("waiting for run {} to complete".format(r.id))
r.wait_status(client.runs.COMPLETE)
