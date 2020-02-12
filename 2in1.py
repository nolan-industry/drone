# import the necessary packages
from __future__ import print_function
from collections import deque
from imutils.video import WebcamVideoStream
import cv2
import imutils
import math
import time
from dronekit import connect, VehicleMode, LocationGlobalRelative, LocationGlobal
from pymavlink import mavutil

# define the lower and upper boundaries of the "green"
# ball in the HSV color space, then initialize the
# list of tracked points
greenLower = (000, 160, 123)
greenUpper = (121, 255, 197)
pts = deque(str(32))

vs = WebcamVideoStream(src=0).start()

time.sleep(2.0)

#connect to copter
vehicle = connect('tcp:127.0.0.1:5763', wait_ready=True)

#Take off
def arm_and_takeoff(aTargetAltitude):
    """
    Arms vehicle and fly to aTargetAltitude.
    """

    print("Basic pre-arm checks")
    # Don't let the user try to arm until autopilot is ready
    while not vehicle.is_armable:
        print(" Waiting for vehicle to initialise...")
        time.sleep(1)

    print("Arming motors")
    # Copter should arm in GUIDED mode
    vehicle.mode = VehicleMode("GUIDED")
    vehicle.armed = True

    while not vehicle.armed:
        print(" Waiting for arming...")
        time.sleep(1)

    print("Taking off!")
    vehicle.simple_takeoff(aTargetAltitude)  # Take off to target altitude

    # Wait until the vehicle reaches a safe height before processing the goto (otherwise the command
    #  after Vehicle.simple_takeoff will execute immediately).
    while True:
        print(" Altitude: ", vehicle.location.global_relative_frame.alt)
        if vehicle.location.global_relative_frame.alt >= aTargetAltitude * 0.95:  # Trigger just below target alt.
            print("Reached target altitude")
            break
        time.sleep(1)

arm_and_takeoff(4)

duration = 5
# add flight control
def condition_yaw(heading, relative=False):
	if relative:
		is_relative = 1  # yaw relative to direction of travel
	else:
		is_relative = 0  # yaw is an absolute angle
	# create the CONDITION_YAW command using command_long_encode()
	msg = vehicle.message_factory.command_long_encode(
		0, 0,  # target system, target component
		mavutil.mavlink.MAV_CMD_CONDITION_YAW,  # command
		0,  # confirmation
		heading,  # param 1, yaw in degrees
		0,  # param 2, yaw speed deg/s
		1,  # param 3, direction -1 ccw, 1 cw
		is_relative,  # param 4, relative offset 1, absolute angle 0
		0, 0, 0)  # param 5 ~ 7 not used
	# send command to vehicle
	vehicle.send_mavlink(msg)

def set_roi(location):

		# create the MAV_CMD_DO_SET_ROI command
	msg = vehicle.message_factory.command_long_encode(
		0, 0,  # target system, target component
		mavutil.mavlink.MAV_CMD_DO_SET_ROI,  # command
		0,  # confirmation
		0, 0, 0, 0,  # params 1-4
		location.lat,
		location.lon,
		location.alt
	)
		# send command to vehicle
	vehicle.send_mavlink(msg)

def get_location_metres(original_location, dNorth, dEast):

	earth_radius = 6378137.0  # Radius of "spherical" earth
	# Coordinate offsets in radians
	dLat = dNorth / earth_radius
	dLon = dEast / (earth_radius * math.cos(math.pi * original_location.lat / 180))

	# New position in decimal degrees
	newlat = original_location.lat + (dLat * 180 / math.pi)
	newlon = original_location.lon + (dLon * 180 / math.pi)
	if type(original_location) is LocationGlobal:
		targetlocation = LocationGlobal(newlat, newlon, original_location.alt)
	elif type(original_location) is LocationGlobalRelative:
		targetlocation = LocationGlobalRelative(newlat, newlon, original_location.alt)
	else:
		raise Exception("Invalid Location object passed")

	return targetlocation;

def get_distance_metres(aLocation1, aLocation2):

	dlat = aLocation2.lat - aLocation1.lat
	dlong = aLocation2.lon - aLocation1.lon
	return math.sqrt((dlat * dlat) + (dlong * dlong)) * 1.113195e5

def get_bearing(aLocation1, aLocation2):

	off_x = aLocation2.lon - aLocation1.lon
	off_y = aLocation2.lat - aLocation1.lat
	bearing = 90.00 + math.atan2(-off_y, off_x) * 57.2957795
	if bearing < 0:
		bearing += 360.00
	return bearing;

def goto_position_target_global_int(aLocation):

	msg = vehicle.message_factory.set_position_target_global_int_encode(
		0,  # time_boot_ms (not used)
		0, 0,  # target system, target component
		mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,  # frame
		0b0000111111111000,  # type_mask (only speeds enabled)
		aLocation.lat * 1e7,  # lat_int - X Position in WGS84 frame in 1e7 * meters
		aLocation.lon * 1e7,  # lon_int - Y Position in WGS84 frame in 1e7 * meters
		aLocation.alt,
		# alt - Altitude in meters in AMSL altitude, not WGS84 if absolute or relative, above terrain if GLOBAL_TERRAIN_ALT_INT
		0,  # X velocity in NED frame in m/s
		0,  # Y velocity in NED frame in m/s
		0,  # Z velocity in NED frame in m/s
		0, 0, 0,  # afx, afy, afz acceleration (not supported yet, ignored in GCS_Mavlink)
		0, 0)  # yaw, yaw_rate (not supported yet, ignored in GCS_Mavlink)
	# send command to vehicle
	vehicle.send_mavlink(msg)

def goto_position_target_local_ned(north, east, down):

	msg = vehicle.message_factory.set_position_target_local_ned_encode(
		0,  # time_boot_ms (not used)
		0, 0,  # target system, target component
		mavutil.mavlink.MAV_FRAME_LOCAL_NED,  # frame
		0b0000111111111000,  # type_mask (only positions enabled)
		north, east, down,  # x, y, z positions (or North, East, Down in the MAV_FRAME_BODY_NED frame
		0, 0, 0,  # x, y, z velocity in m/s  (not used)
		0, 0, 0,  # x, y, z acceleration (not supported yet, ignored in GCS_Mavlink)
		0, 0)  # yaw, yaw_rate (not supported yet, ignored in GCS_Mavlink)
	# send command to vehicle
	vehicle.send_mavlink(msg)

def goto(dNorth, dEast, gotoFunction=vehicle.simple_goto):

	currentLocation = vehicle.location.global_relative_frame
	targetLocation = get_location_metres(currentLocation, dNorth, dEast)
	targetDistance = get_distance_metres(currentLocation, targetLocation)
	gotoFunction(targetLocation)

	# print "DEBUG: targetLocation: %s" % targetLocation
	# print "DEBUG: targetLocation: %s" % targetDistance

	while vehicle.mode.name == "GUIDED":  # Stop action if we are no longer in guided mode.
		# print "DEBUG: mode: %s" % vehicle.mode.name
		remainingDistance = get_distance_metres(vehicle.location.global_relative_frame, targetLocation)
		print("Distance to target: ", remainingDistance)
		if remainingDistance <= targetDistance * 0.01:  # Just below target, in case of undershoot.
			print("Reached target")
			break;
		time.sleep(2)

def send_ned_velocity(velocity_x, velocity_y, velocity_z, duration):

	msg = vehicle.message_factory.set_position_target_local_ned_encode(
		0,  # time_boot_ms (not used)
		0, 0,  # target system, target component
		mavutil.mavlink.MAV_FRAME_LOCAL_NED,  # frame
		0b0000111111000111,  # type_mask (only speeds enabled)
		0, 0, 0,  # x, y, z positions (not used)
		velocity_x, velocity_y, velocity_z,  # x, y, z velocity in m/s
		0, 0, 0,  # x, y, z acceleration (not supported yet, ignored in GCS_Mavlink)
		0, 0)  # yaw, yaw_rate (not supported yet, ignored in GCS_Mavlink)

	# send command to vehicle on 1 Hz cycle
	for x in range(0, duration):
		vehicle.send_mavlink(msg)
		time.sleep(1)

def send_global_velocity(velocity_x, velocity_y, velocity_z, duration):

	msg = vehicle.message_factory.set_position_target_global_int_encode(
		0,  # time_boot_ms (not used)
		0, 0,  # target system, target component
		mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,  # frame
		0b0000111111000111,  # type_mask (only speeds enabled)
		0,  # lat_int - X Position in WGS84 frame in 1e7 * meters
		0,  # lon_int - Y Position in WGS84 frame in 1e7 * meters
		0,  # alt - Altitude in meters in AMSL altitude(not WGS84 if absolute or relative)
		# altitude above terrain if GLOBAL_TERRAIN_ALT_INT
		velocity_x,  # X velocity in NED frame in m/s
		velocity_y,  # Y velocity in NED frame in m/s
		velocity_z,  # Z velocity in NED frame in m/s
		0, 0, 0,  # afx, afy, afz acceleration (not supported yet, ignored in GCS_Mavlink)
		0, 0)  # yaw, yaw_rate (not supported yet, ignored in GCS_Mavlink)

	# send command to vehicle on 1 Hz cycle
	for x in range(0, duration):
		vehicle.send_mavlink(msg)
		time.sleep(1)


# keep looping
while True:
	# grab the current frame
	frame = vs.read()

	# resize the frame, blur it, and convert it to the HSV
	# color space
	frame = imutils.resize(frame, width=600)
	blurred = cv2.GaussianBlur(frame, (11, 11), 0)
	hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
	# construct a mask for the color "green", then perform
	# a series of dilations and erosions to remove any small
	# blobs left in the mask
	mask = cv2.inRange(hsv, greenLower, greenUpper)
	mask = cv2.erode(mask, None, iterations=2)
	mask = cv2.dilate(mask, None, iterations=2)

	# find contours in the mask and initialize the current
	# (x, y) center of the ball
	cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
							cv2.CHAIN_APPROX_SIMPLE)
	cnts = imutils.grab_contours(cnts)
	center = None
	# only proceed if at least one contour was found
	if len(cnts) > 0:
		# find the largest contour in the mask, then use
		# it to compute the minimum enclosing circle and
		# centroid
		c = max(cnts, key=cv2.contourArea)
		((x, y), radius) = cv2.minEnclosingCircle(c)
		M = cv2.moments(c)
		center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
		# only proceed if the radius meets a minimum size
		if radius > 10:
			# draw the circle and centroid on the frame,
			# then update the list of tracked points
			cv2.circle(frame, (int(x), int(y)), int(radius),
					   (0, 255, 255), 2)
			cv2.circle(frame, center, 5, (0, 0, 255), -1)
	# update the points queue
	pts.appendleft(center)



	# show the frame to our screen
	#cv2.imshow("Frame", frame)
	#key = cv2.waitKey(1) & 0xFF

	miss = 0 # set a timer, if no object detected in 10sec, break and RTL
	while center is None:
		print("no object")
		miss += 1
		print(miss)
		time.sleep(1)

		frame = vs.read()

		# resize the frame, blur it, and convert it to the HSV
		# color space
		frame = imutils.resize(frame, width=600)
		blurred = cv2.GaussianBlur(frame, (11, 11), 0)
		hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
		# construct a mask for the color "green", then perform
		# a series of dilations and erosions to remove any small
		# blobs left in the mask
		mask = cv2.inRange(hsv, greenLower, greenUpper)
		mask = cv2.erode(mask, None, iterations=2)
		mask = cv2.dilate(mask, None, iterations=2)

		# find contours in the mask and initialize the current
		# (x, y) center of the ball
		cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
								cv2.CHAIN_APPROX_SIMPLE)
		cnts = imutils.grab_contours(cnts)
		center = None
		# only proceed if at least one contour was found
		if len(cnts) > 0:
			# find the largest contour in the mask, then use
			# it to compute the minimum enclosing circle and
			# centroid
			c = max(cnts, key=cv2.contourArea)
			((x, y), radius) = cv2.minEnclosingCircle(c)
			M = cv2.moments(c)
			center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
			# only proceed if the radius meets a minimum size
			if radius > 10:
				# draw the circle and centroid on the frame,
				# then update the list of tracked points
				cv2.circle(frame, (int(x), int(y)), int(radius),
						   (0, 255, 255), 2)
				cv2.circle(frame, center, 5, (0, 0, 255), -1)
		# update the points queue
		pts.appendleft(center)


		# show the frame to our screen
		#cv2.imshow("Frame", frame)
		#key = cv2.waitKey(1) & 0xFF

		if miss > 10:
			break

	else:
		center = (x,y)
		print(x)
		print(y)
		miss = 0
		time.sleep(1)



		while x < 290:
			condition_yaw(-15,relative=True)
			send_global_velocity(0,0,0,3)
		while x > 310:
			condition_yaw(15,relative=True)
			send_global_velocity(0,0,0,3)



	if miss > 10:
		print("Returning to Launch")
		vehicle.mode = VehicleMode("RTL")

	# if the 'q' key is pressed, stop the loop
	#if key == ord("q"):
		#break
# if we are not using a video file, stop the camera video stream

vs.stop()
# close all windows
cv2.destroyAllWindows()
