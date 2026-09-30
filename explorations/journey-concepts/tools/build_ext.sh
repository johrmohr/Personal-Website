#!/bin/zsh
# build_ext.sh <key> <extension.mp4> <raw loop.mp4 | tail> [r0=1] [ramp=1.5] [skip=0] [nasa=bh-journey.mp4] [threshold=170]
# media/journey_<key>.mp4, one video: bh-journey frames 0–207 (NASA until just before its arch forms), then Seedance's forward
# extension of that footage. Its first <ramp> s play <r0>x fast, easing to 1x, so the join keeps NASA's pace; <skip> frames are
# dropped from its start. <nasa> is the footage the extension continued (frames 0–207; the cue clips have the disc painted in).
#   raw loop: a separate Higgsfield loop (same frame at both ends); the extension's last 0.5 s blends into it, picked up at 0.5 s.
#             tools/align_tail.py first lines the two up (disc and horizon; <threshold> finds the disc), so the blend can't slide
#   tail:     the loop is the extension's own last 4 s (it must hold still by then); the journey runs straight into it at 0 s
set -e
JC=/Users/jordanmoreno/Desktop/Personal-Website/explorations/journey-concepts; k=$1; EXT=${2:A}; LOOP=$3; R0=${4:-1}; RAMP=${5:-1.5}; SKIP=${6:-0}; NASA=${7:-$JC/bh-journey.mp4}; NASA=${NASA:A}; THR=${8:-170}; TOOLS=${0:A:h}
[[ $LOOP != tail ]] && LOOP=${LOOP:A}
W=${TMPDIR:-/tmp}/journey_ext_$k; mkdir -p $W; cd $W
enc=(-c:v libx264 -crf 10 -preset veryfast -pix_fmt yuv420p -an)
nframes() { ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 $1; }

# 1. the extension at 1920x1080 (drafts come at 480p), without its first SKIP frames
ffmpeg -loglevel error -y -i $EXT -vf "trim=start_frame=$SKIP,setpts=PTS-STARTPTS,scale=1920:1080:flags=lanczos,setsar=1" -r 24 $enc ext.mp4
NE=$(nframes ext.mp4)

if [[ $LOOP == tail ]]; then
  # 2a. loop = the extension's last 96 frames: frames 24–71, then 72–95 crossfading into 0–23 (seamless at both ends);
  #     the journey stops just before frame 24, so it runs straight into the loop
  S0=$((NE - 96))
  ffmpeg -loglevel error -y -i ext.mp4 -filter_complex "[0:v]trim=start_frame=$S0,setpts=PTS-STARTPTS,split=3[a][b][c];[a]trim=end_frame=24,setpts=PTS-STARTPTS[head];[b]trim=start_frame=24:end_frame=72,setpts=PTS-STARTPTS[body];[c]trim=start_frame=72,setpts=PTS-STARTPTS[tail];[tail][head]blend=all_expr='A*(1-T/0.9583)+B*(T/0.9583)'[mix];[body][mix]concat=n=2:v=1:a=0,format=yuv420p[out]" -map "[out]" -c:v libx264 -preset slow -crf 18 -movflags +faststart -an loopS.mp4
  NE=$((S0 + 24)); ffmpeg -loglevel error -y -i ext.mp4 -vf "trim=end_frame=$NE,setpts=PTS-STARTPTS" $enc extB.mp4; LIN=0
else
  # 2b. the Higgsfield loop made seamless (last second crossfades into the first); the extension's last 12 frames blend into
  #     loop frames 0–11 and the page picks the loop up at 0.5 s
  ffmpeg -loglevel error -y -i $LOOP -vf "scale=1920:1080:flags=lanczos,setsar=1" -r 24 $enc rawloop.mp4; NL=$(nframes rawloop.mp4)
  python3 $TOOLS/align_tail.py ext.mp4 rawloop.mp4 $THR
  ffmpeg -loglevel error -y -i ext.mp4 -vf "$(cat ext_filter.txt)" $enc extA.mp4 && mv extA.mp4 ext.mp4
  ffmpeg -loglevel error -y -i rawloop.mp4 -vf "$(cat loop_filter.txt)" $enc loopA.mp4 && mv loopA.mp4 rawloop.mp4
  ffmpeg -loglevel error -y -i rawloop.mp4 -filter_complex "[0:v]split=3[a][b][c];[a]trim=end_frame=24,setpts=PTS-STARTPTS[head];[b]trim=start_frame=24:end_frame=$((NL - 24)),setpts=PTS-STARTPTS[body];[c]trim=start_frame=$((NL - 24)),setpts=PTS-STARTPTS[tail];[tail][head]blend=all_expr='A*(1-T/0.9583)+B*(T/0.9583)'[mix];[mix][body]concat=n=2:v=1:a=0,format=yuv420p[out]" -map "[out]" -c:v libx264 -preset slow -crf 18 -movflags +faststart -an loopS.mp4
  ffmpeg -loglevel error -y -i ext.mp4 -i loopS.mp4 -filter_complex "[0:v]split=2[g1][g2];[g1]trim=end_frame=$((NE - 12)),setpts=PTS-STARTPTS[gh];[g2]trim=start_frame=$((NE - 12)),setpts=PTS-STARTPTS[gt];[1:v]trim=end_frame=12,setpts=PTS-STARTPTS[lh];[gt][lh]blend=all_expr='A*(1-T/0.4583)+B*(T/0.4583)'[gm];[gh][gm]concat=n=2:v=1:a=0[out]" -map "[out]" $enc extB.mp4; LIN=0.5
fi

# 3. 120 fps motion-interpolated, speed R0 easing linearly to 1 over the first RAMP s, resampled to 30 fps
TE=$(python3 -c "print(($NE - 1) / 24)")
read KK O1 SHOT N <<< $(python3 -c "
import math; r0, T1, te = $R0, $RAMP, $TE
kk = (1 - r0) / T1; o1 = math.log(1 / r0) / kk if r0 != 1 else T1; shot = o1 + te - T1
print(kk if r0 != 1 else 0, o1, round(shot, 4), round(shot * 30) + 1)")
if [[ $R0 == 1 ]]; then MAP="T"; else MAP="if(lt(T\,$RAMP)\,log(($R0+($KK)*T)/$R0)/($KK)\,$O1+T-$RAMP)"; fi
ffmpeg -loglevel error -y -i extB.mp4 -vf "minterpolate=fps=120:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,setpts='($MAP)/TB',fps=30,trim=end_frame=$N" $enc extR.mp4

# 4. NASA's frames 0–207, upscaled, then the extension: one 30 fps video
ffmpeg -loglevel error -y -i $NASA -i extR.mp4 -filter_complex "[0:v]trim=end_frame=208,setpts=PTS-STARTPTS,scale=1920:1080:flags=lanczos,setsar=1[a];[1:v]setpts=PTS-STARTPTS,setsar=1[b];[a][b]concat=n=2:v=1:a=0,format=yuv420p[out]" -map "[out]" -r 30 -c:v libx264 -preset slow -crf 21 -g 30 -movflags +faststart -an $JC/media/journey_$k.mp4
cp loopS.mp4 $JC/media/loop_$k.mp4
# the site preview plays tools/make_site_cut.py's cut of this video (and its reversed copy); run it next

# 5. stills for exports, meta.json (the shot's length after the handoff, where the loop picks up)
for n in journey_$k loop_$k; do rm -rf $JC/frames/$n; mkdir -p $JC/frames/$n; ffmpeg -loglevel error -y -i $JC/media/$n.mp4 -q:v 3 $JC/frames/$n/f_%04d.jpg; done
nj=$(ls $JC/frames/journey_$k | wc -l | tr -d ' '); nl=$(ls $JC/frames/loop_$k | wc -l | tr -d ' ')
echo "journey_$k: $nj frames ($(du -h $JC/media/journey_$k.mp4 | cut -f1)), shot $SHOT s after the handoff; loop_$k: $nl frames, picked up at $LIN s"
python3 - $JC/media/meta.json $k $nj $nl $SHOT $LIN <<'EOF'
import json, os, sys
p, k, nj, nl, shot, lin = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6])
m = json.load(open(p)) if os.path.exists(p) else {}
m[f'journey_{k}'] = {'fps': 30, 'n': nj, 'shot': shot}; m[f'loop_{k}'] = {'fps': 24, 'n': nl, 'in': lin}
json.dump(m, open(p, 'w'), indent=1, sort_keys=True)
EOF
a=$(ffmpeg -i $JC/frames/loop_$k/f_$(printf %04d $nl).jpg -i $JC/frames/loop_$k/f_0001.jpg -lavfi psnr -f null - 2>&1 | grep -o "average:[0-9.inf]*"); echo "loop wrap (last vs first) $a"
li=$(python3 -c "print(round($LIN * 24) + 1)")
b=$(ffmpeg -i $JC/frames/journey_$k/f_$(printf %04d $nj).jpg -i $JC/frames/loop_$k/f_$(printf %04d $li).jpg -lavfi psnr -f null - 2>&1 | grep -o "average:[0-9.inf]*"); echo "journey end vs the loop where it picks up $b"
