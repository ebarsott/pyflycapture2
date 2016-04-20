#!/usr/bin/env python

import cPickle as pickle
import sys
import time

import cv2
has_cv2 = True
import numpy
import pygame
import pylab

import flycapture2


fgraph_dx = 4
fgraph_height = 200
fgraph_width = 200

frame_rate = 30

csize = (4, 11)


handle = 0
if len(sys.argv) > 1:
    handle = sys.argv[1]
    try:
        i = int(handle)
        handle = i
    except:
        pass
etime = 1000  # ms
if len(sys.argv) > 2:
    etime = int(sys.argv[2])

print "Opening camera: %s" % handle
c = flycapture2.PointGrey(handle)
#print "Opened camera: %s" % c.SerialNumber
#c.CycleMode = 'Continuous'
#print "Cycle Mode: %s" % c.CycleMode
#c.ExposureTime = etime / 1000.  # 10 fps
#if hasattr(c, 'BitDepth'):
#    assert c.BitDepth == '16 Bit'

s, _, p = c.get_format7_settings()
#s.height = 1920
#s.width = 1080
s.set_pixel_format('rgb8')
c.set_format7_settings(s, p)
#h = c.AOIHeight
h = s.height
#w = c.AOIWidth
w = s.width
d = numpy.uint8
#print "Image Size = %s x %s x %s" % (h, w, d)

scale = 2
frame_count = 0


print "Starting pygame"
pygame.init()
screen = pygame.display.set_mode(
    (w/scale, h/scale),
    pygame.HWSURFACE | pygame.DOUBLEBUF,
    32)
pygame.display.set_caption("Live Video")
clock = pygame.time.Clock()

print "Queuing buffers"
#c.buffers.nbytes = c.ImageSizeBytes

print "Start Acquisition"
#c.start_acquisition()
im = None
bg = None
stretch = False
focus = False
focus_values = []
max_focus = -float('inf')
quit = False
recording = False
video = None
video_index = 0
zoom = 1
grab_calibration = False
cpts = []
while not quit:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            #c.stop_acquisition()
            quit = True
            continue
        if event.type == pygame.KEYDOWN:
            print "Keypressed: %s" % event.key
            if event.key == pygame.K_SPACE:
                if im is not None:
                    fn = '%i.tif' % int(time.time())
                    print "Saving image to %s" % fn
                    pylab.imsave(fn, im, cmap=pylab.cm.gray)
            delta_etime = None
            if event.key == pygame.K_UP:
                delta_etime = 50
            if event.key == pygame.K_RIGHT:
                delta_etime = 10
            if event.key == pygame.K_DOWN:
                delta_etime = -50
            if event.key == pygame.K_LEFT:
                delta_etime = -10
            if event.key == pygame.K_c:
                grab_calibration = True
            if event.key == pygame.K_s:
                stretch = not stretch
            if event.key == pygame.K_f:
                focus = not focus
            if event.key == pygame.K_z:
                zoom += 1
            if event.key == pygame.K_x:
                zoom -= 1
                if zoom < 1:
                    zoom = 1
            if event.key == pygame.K_r:
                if has_cv2:
                    recording = not recording
                    if recording:
                        print "Started recording: %s" % video_index
                        if has_cv2:
                            video = cv2.VideoWriter(
                                '%03i.avi' % video_index,
                                cv2.VideoWriter_fourcc('X', 'V', 'I', 'D'),
                                frame_rate, (w, h))
                            video_index += 1
                    else:
                        print "Stopped recording"
                        if video is not None:
                            video.release()
                            video = None
            if event.key == pygame.K_b:
                if bg is None:
                    bg = im
                else:
                    bg = None
            if event.key == pygame.K_q:
                quit = True
                continue
            if delta_etime is not None:
                etime = max(10, min(etime + delta_etime, 30000))
                #c.ExposureTime = etime / 1000.
                print "Set exposure time to %i" % etime

    #print "\tQueuing buffer"
    #c.buffers.queue()
    #im = c.capture()
    im, _ = c.grab('rgb8', stop=False)
    if grab_calibration:
        ret, cir = cv2.findCirclesGrid(
            im, csize, flags=cv2.CALIB_CB_ASYMMETRIC_GRID)
        grab_calibration = False
        if ret:
            cpts.append(cir)
            print("Found grid: %s" % len(cpts))
        else:
            print("Could not find grid")

    if has_cv2 and recording and video is not None:
        video.write(im[:, :, ::-1])
    #print im.min(), im.max(), im.mean(), im.std()
    im = im[::scale, ::scale, :]
    im = numpy.swapaxes(im, 0, 1)
    #print "\tCapture: %s" % r
    #print(im[0, 0])
    #if bg is not None:
    #    #im -= bg
    #    im = im / (bg.astype('f8') + 0.000001)
    #    #print(im.min(), im.max())
    #    im = ((im - im.min()) / (im.max() - im.min()) * 2 ** 16.).astype('u2')
    #    #im = (im * 255).astype('u2')
    #print "Display frame %s" % frame_count
    #clip = (im[::scale, ::scale].T).astype('uint32')
    #if stretch:
    #    clip = clip - clip.min()
    #    clip *= (255. / clip.max())
    #sim = pygame.surfarray.map_array(screen, im)
    pygame.surfarray.blit_array(
        screen,
        im.astype('uint32'))
    #pygame.surfarray.blit_array(
    #    screen,
    #    im.astype('uint32'))
    #pygame.surfarray.blit_array(
    #    screen,
    #    numpy.dstack((clip, clip, clip)))
    #if focus:
    #    focus_values.append(compute_focus(im[512:1536, 512:1536]))
    #    # draw focus array
    #    max_length = int(fgraph_width / fgraph_dx)
    #    if len(focus_values) > max_length:
    #        focus_values = focus_values[-max_length:]
    #    max_focus = max(max_focus, max(focus_values))
    #    #s = fgraph_height / (max(focus_values) - min(focus_values))
    #    s = fgraph_height / (max_focus - min(focus_values))
    #    o = min(focus_values)
    #    points = [
    #        (i * fgraph_dx, fgraph_height - ((v - o) * s)) for i, v
    #        in enumerate(focus_values)]
    #    pygame.draw.line(
    #        screen, pygame.Color('blue'),
    #        (fgraph_width, 0), (fgraph_width, fgraph_height), 1)
    #    if len(points) > 1:
    #        pygame.draw.lines(screen, pygame.Color('red'), False, points, 2)
    clock.tick(frame_rate)
    #print("flip")
    pygame.display.flip()
    frame_count += 1
if len(cpts):
    print("Saving cpts to cpts")
    with open('cpts.p', 'w') as f:
        pickle.dump(cpts, f)
c.disconnect()
sys.exit()
if has_cv2:
    if video is not None:
        video.release()
