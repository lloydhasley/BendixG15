#
# code extracts the output from the music program.
#
# after block writes to either Line 2 or Line 3
# and extracts that data, determines if it is a
# square wave or not.  if a square wave, it 
# extracts the period, converts it to a frequency
# and writes it to a hardcoded file.
#
#from selectors import SelectSelector
#from pyaudio import PyAudio
import pyaudio
import threading
import time

from G15Constants import *

ALLOWABLE_LEN_VARIATION = 4
ALLOWABLE_LEN_VARIATION = 40
MIN_RUN_LEN = 20

FRAMERATE_f = 1000000 / BIT_TIME		# bit frequency
FRAMERATE = int(FRAMERATE_f)

music_debug = 0

p= pyaudio.PyAudio()


class EmulMusic:
	def __init__(self, g15):
		self.g15 = g15
		self.cpu = g15.cpu

		self.cur_position = 0
		self.frequency = 0
		self.volume = 100

		# dummies to keep pep8 happy
		self.word = 0

		self.notdone = 1
		self.music_enable = False

		self.capture_tracks = { 2:1, 3:1, 19:1}
		self.musicdb = {}

		if music_debug:
			print(". BIT_TIME: ", BIT_TIME)
			print(" WORD_TIME: ", WORD_TIME)
			print("TRACK_TIME: ", TRACK_TIME)

		self.outstream = None
		self.playtrack = 2
		self.stream_toplay = []

		self.thread_run = True
		self.t2 = threading.Thread(target=self.play, daemon=True)

	def close(self):
		self.thread_run = False
		if self.outstream:
			self.outstream.close()

	def play(self):
		# music plays in a separate thread
		while(self.thread_run):
			if self.music_enable and self.outstream and self.stream_toplay != []:
				self.outstream.write(self.stream_toplay)
			else:
				time.sleep(0.01)

	def enable(self, music_enable):
		if not music_enable:
			self.music_enable = False
			self.stream_toplay = []

		if music_enable and not self.music_enable:
			# no music_enable ==> yes music_enable
			self.search()

			self.outstream = p.open(format=p.get_format_from_width(1),
					channels=1,
					rate=FRAMERATE,
					output=True
				)

		else:
			if self.outstream:
				self.outstream.close()

		if music_enable:
			print("setting music enable")
			self.music_enable = True
			self.stream_toplay = []

	def trackcopy(self, instruction):
		# we have a track copy instruction execution into a possible music track (2,3,19)
		#
		if not self.music_enable:
			print("music is not enabled")
			return

		current_time = self.g15.drum.time_get_str()
		d = instruction['d']
		s = instruction['s']

		if d not in self.capture_tracks:
			return

		if s in self.musicdb:
			db_entry = self.musicdb[s]
			frequency = db_entry['frequency']
			samples = db_entry['samples']
			stream = db_entry['stream']
		else:
			frequency = 0

		if music_debug:
			print("music s:%02d" % s, " -> d:%02d" % d, ' freq=%6.1f' % frequency,
				  " at time: ", current_time)

		if d == self.playtrack:
			self.stream_toplay = stream

	def search(self):
		count = 0
		tracks = list(range(20))
		tracks.append(29)

		for i in tracks:
			retval = self.extract(i)
			if retval:
				count += 1
				print("track: %2d" % i, "%6.1f" % self.musicdb[i]['frequency'], "Hz",
					  " max variation from square: ", self.musicdb[i]['max_variation'])
			else:
				print("track: %2d" % i, " not a music track")

		if count <= 10:
			self.notdone = 1

	def extract(self, track):
		self.cur_position = 0

		if self.notdone:
			self.notdone = 0
			self.search()

		if track == 29:
			self.frequency = 0
		else:
			db = self.extract_db(track)
			# note: bits is a list of [bit values, run_lengths]
			self.max_variation, self.frequency = self.determine_if_square(track, db)

		samples = self.mk_stream(track)
		stream = bytes(samples)

		entry = {'frequency': self.frequency, 'max_variation': self.max_variation, 'samples': samples, 'stream': stream }
		self.musicdb[track] = entry
		return True

	def mk_stream(self, track):
		samples = []
		for word in range(WORDS_PER_TRACK):
			data_word = self.g15.drum.read(track, word)
			for bit_pos in range(WORD_SIZE):
				bit = (data_word >> bit_pos) & 1
				sample = bit * self.volume
				samples.append(sample)

		return samples

	def extract_db(self, track):
		#
		# change drum bit information into a
		# list of run_lengths
		#
		# ignores first and last lengths
		#
		db = [[], []]
		bit_last = 0
		bit_last_pos = 0
		run_length = 0

		for i in range(BITS_PER_TRACK):
			bit = self.extract_bit(track, i)

			if i == 0:
				bit_last = bit
				bit_last_pos = 0
				run_length = 0
				continue

			if bit_last != bit:
				if bit_last_pos != 0:
					#  ignore first run
					db[bit_last].append(run_length)
				bit_last = bit
				run_length = 1
				bit_last_pos = i
			else:		# bits match
				run_length += 1
		
		return db		# really run_lengths

	def extract_bit(self, track, bit_position):
		word_pos = bit_position % WORD_SIZE
		word_id = bit_position // WORD_SIZE
		word = self.g15.drum.read(track, word_id)
		bit = (word >> word_pos) & 1
		return bit

	# @staticmethod
	def determine_if_square(self, track, db):
		if track == 2:
			return 0, 0

		# print("TRACK = ", track)
		average_length = []
		for value in [0, 1]:
			if len(db[value]) == 0:
				return 0, 0

			#  determine average run_length
			totalsum = 0
			for run_length in db[value]:
				totalsum += run_length
			sum_average = totalsum / len(db[value])
			average_length.append(sum_average)

			# determine run length variation
			max_variation = 0
			tooshort = 0
			for run_length in db[value]:
				variation = abs(run_length - sum_average)
				if variation > max_variation:
					max_variation = variation
				if run_length < MIN_RUN_LEN:
					tooshort = 1

			if music_debug:
				print("NO SQUARE WAVE DETECTED on track: ", track)
				print(" max observed variation: ", max_variation)
				print(" tooshort: ", tooshort)
				return 0, 0

		# have a square wave
		period_length = average_length[0] + average_length[1]
		period = period_length * BIT_TIME		# in uS
		frequency = 1000000.0 / period			# in Hz

		return max_variation, frequency

	# currently not used
	def extract_bits(self, track):
		if (self.cur_position % 29) == 0:
			wordaddr = self.cur_position // 29
			self.word = self.g15.drum.read(track, wordaddr)
			word, bit = self.position2wordbit(self.word)
			return word, bit

	@staticmethod
	def position2wordbit(position):
		bit = position % 29
		word = position // 29
		return word, bit

	def write(self):
		pass
