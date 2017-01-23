#!/usr/bin/python

# COPYRIGHT AND PERMISSION NOTICE
# Penn Neural Recording and Stimulation Software
# Copyright (C) 2015 The Trustees of the University of Pennsylvania. All rights reserved.
#
# SOFTWARE LICENSE
# The Trustees of the University of Pennsylvania ("Penn") and the
# Computational Memory Lab ("Developer") of Penn Neural Recording and Stimulation
# Software ("Software") give recipient ("Recipient") permission to download a
# single copy of the Software in executable form and use for non-profit academic
# research purposes only provided that the following conditions are met:
#
# 1)	Recipient may NOT use the Software for any clinical or diagnostic
#       purpose, including clinical research other than for the purpose of
#       fulfilling Recipient's obligations under the subaward agreement between
#       Penn and Recipient under Prime Award No. N66001-14-2-4-3 awarded by the
#       Defense Advanced Research Projects Agency to Penn ("Subaward").
#
# 2)	Recipient may NOT use the Software for any commercial benefit.
#
# 3)	Recipient will not copy the Software, other than to the extent necessary
#       to fulfill Recipient's obligations under the Subaward.
#
# 4)	Recipient will not sell the Software.
#
# 5)	Recipient will not give the Software to any third party.
#
# 6)	Recipient will provide the Developer with feedback on the use of the
#       Software in their research.  Recipient agrees that the Developers and
#       Penn are freely permitted to use any information Recipient provides in
#       making changes to the Software. All feedback, bug reports and technical
#       questions shall be sent to:
#           Dan Rizzuto: drizzuto@sas.upenn.edu
#
# 7)	Any party desiring a license to use the Software for commercial purposes
#       shall contact:
#           The Penn Center for Innovation at 215-898-9591.
#
# 8)	Recipient will destroy all copies of the Software at the completion of
#       its obligations under its Subaward.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS, CONTRIBUTORS, AND THE
# TRUSTEES OF THE UNIVERSITY OF PENNSYLVANIA "AS IS" AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
# EVENT SHALL THE COPYRIGHT OWNER, CONTRIBUTORS OR THE TRUSTEES OF THE
# UNIVERSITY OF PENNSYLVANIA BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

from extendedPyepl import *
from pyepl import timing

# other modules
import codecs  # FOR READING UNICODE
import random
import os
import sys
import shutil
import unicodedata
import playIntro
from RAMControl import RAMControl
from messages import WordMessage

ram_control = RAMControl.instance()

# Set the current version
# TODO: Update the version for System 2.0 pyepl changes
MIN_PYEPL_VERSION = '1.0.0'


class Utils:

    def __init__(self):
        pass

    @staticmethod
    def shuffle_together(*lists):
        zipped_lists = zip(*lists)
        random.shuffle(zipped_lists)
        return zip(*zipped_lists)

    @staticmethod
    def shuffle_inner_lists(lists):
        """
        Shuffles items within each list in place
        :param lists: 2D list of size nLists x wordsPerList
        """
        for l in lists:
            random.shuffle(l)

    @staticmethod
    def seed_rng(seed):
        """
        Seeds the random number generator with the input argument
        :param seed: the element to seed Random with
        """
        random.seed(seed)

    @staticmethod
    def remove_accents(input_str):
        nkfd_form = unicodedata.normalize('NFKD', input_str)
        return u"".join([c for c in nkfd_form if not unicodedata.combining(c)])


class PALExperiment:

    def __init__(self, exp, config, video, clock,):
        """
        Initialize the data for the experiment.
        Runs the prepare function, sets up the experiment state
        :param exp: Experiment object
        :param config: Config object
        :param video: VideoTrack object
        """
        self.exp, self.config = \
            exp, config
        self.subject = exp.getOptions().get('subject')
        self.experiment_name = config.experiment
        self.video = video
        self.clock = clock
        self.wp = CustomTextPool(self.config.wp)

    def _show_prepare_message(self):
        """
        Shows "Preparing trials in..."
        """
        self.video.clear('black')
        self.video.showCentered(Text(
            """
** PREPARING TRIALS IN %(language)s **
If this is not correct,
exit the experiment,
then delete the subject folder in:
/Users/exp/RAM_2.0/data/%(exp)s/%(subj)s
        """ % {'language': 'ENGLISH' if self.config.LANGUAGE == 'EN' else 'SPANISH',
               'exp': self.experiment_name,
               'subj': self.subject}))
        self.video.updateScreen()
        self.clock.delay(1000)
        self.clock.wait()

    def _copy_word_pool(self):
        """
        Copies the word pool with and without accents to session folder
        """
        sess_path = self.exp.session.fullPath()
        # With accents
        shutil.copy(self.config.wp, os.path.join(sess_path, '..'))
        # Without accents
        no_accents_wp = [Utils.remove_accents(line.strip())
                         for line in codecs.open(self.config.wp, 'r', 'utf-8').readlines()]
        open(os.path.join(sess_path, '..', self.config.noAcc_wp), 'w').write('\n'.join(no_accents_wp))

    def _assert_good_list_params(self):
        assert(self.config.nBaselineTrials + self.config.nStimTrials + self.config.nControlTrials ==
               self.config.nTrials)

    def _verify_files(self):
        """
        Verify that all the files specified in the config are there so
        that there is no random failure in the middle of the experiment.

        This will call sys.exit(1) if any of the files are missing.
        """
        config = self.config
        if config.LANGUAGE != 'EN' and config.LANGUAGE != 'SP':
            print '\nERROR:\nLanguage must be set to "EN" or "SP"'
            sys.exit(1)

        # make the list of files from the config vars
        files = (config.wp,
                 config.pre_practiceList,
                 config.post_practiceList,
                 config.practice_wordList,
                 )

        for f in files:
            if not os.path.exists(f):
                print "\nERROR:\nPath/File does not exist: %s\n\nPlease verify the config.\n" % f
                sys.exit(1)

    def _get_stim_session_sources(self):
        """
        will return the filenames to be read for all sessions
        that are counterbalanced for stim positions
        :return: the filenames for each session
        """
        sess_numbers = [[i, i+1] for i in range(1, self.config.numSessions+1, 2)]
        print(sess_numbers)
        random.shuffle(sess_numbers)
        session_sources = []
        for sess_pair in sess_numbers:
            random.shuffle(sess_pair)
            session_sources.extend(
                [os.path.join(self.config.wordList_dir % self.config.LANGUAGE,
                              '%d.txt' % sess_num)
                    for sess_num in sess_pair])
        return session_sources

    def _get_nonstim_session_sources(self):
        """
        Gets the filenames to be read for all sessions to be
        used for the non-stim experiment
        :return: the filename for each session
        """
        session_sources = range(1, self.config.numSessions+1)
        random.shuffle(session_sources)
        return [os.path.join(self.config.wordList_dir % self.config.LANGUAGE,
                             '%d.txt' % sess_num)
                for sess_num in session_sources]

    def _get_session_sources(self):
        """
        Gets the filenames to be read for all sessions to be
        used for any type of experiment
        :return: the filename for each session
        """
        if self.is_stim_experiment():
            return self._get_stim_session_sources()
        else:
            return self._get_nonstim_session_sources()

    def _read_session_source(self, session_source_file):
        """
        Reads the words from a session source file into a 2D array
        :param session_source_file: the filename to be read
        :return: 2D array of words
        """
        session_lists = [x.strip().split() for x in codecs.open(session_source_file, encoding='utf-8').readlines()]

        # Check to make sure they're all the right length
        assert all([len(this_list) == self.config.listLen for this_list in session_lists])

        # Convert into TextPool items
        return [[self.wp.findBy(name=word) for word in trial] for trial in session_lists]

    def is_stim_experiment(self):
        """
        :return: Whether or not this is a stim session
        """
        stim_type = self.config.stim_type
        if stim_type == 'CLOSED_STIM':
            return True
        elif stim_type == 'NO_STIM':
            return False
        else:
            raise Exception('STIM TYPE:%s not recognized' % stim_type)

    def _prepare_single_session_lists(self):
        """
        Creates the lists for a single session
        :return:(pairs, cue_dirs, test_order, list_is_stim)
        """
        # Shuffle within the lists
        (pairs, cue_dirs, test_order) = self._make_session_lists()

        # Put the baseline trials at the front and assign stim to lists
        list_is_stim = self._assign_stim_to_lists()

        return pairs, cue_dirs, test_order, list_is_stim

    def _assign_stim_to_lists(self):
        """
        pseudo-randomly assigns stim to trials such that each half of trials have an
        equal number of stim and non-stim lists
        :return: stim_on_list
        """
        stim_halves = (0, self.config.nStimTrials/2, self.config.nStimTrials)
        nonstim_halves = (0, self.config.nControlTrials/2, self.config.nControlTrials)

        stims = [False]*self.config.nBaselineTrials
        for i in range(2):
            half_stims = [True]*(stim_halves[i+1]-stim_halves[i]) + \
                         [False]*(nonstim_halves[i+1]-nonstim_halves[i])
            random.shuffle(half_stims)
            stims += half_stims
        return stims

    def _split_session_lists_by_stim_type(self, session_lists):
        """
        Splits lists into stim lists and nonstim lists
        NOTE: Assumes that the lists in the input are in the order:
            [*<stim_lists>, *<nonstim_lists>]
        :param session_lists: 2D matrix of size nLists x wordsPerList of all possible lists
        :return: (stim_lists, nonstim_lists)
        """
        stim_lists = session_lists[:self.config.nStimTrials]
        nonstim_lists = session_lists[self.config.nStimTrials:]
        return stim_lists, nonstim_lists

    def _prepare_practice_lists(self):
        """
        Prepares the words for the practice list
        """
        practice_words = [line.strip() for line in
                          codecs.open(self.config.practice_wordList,
                                      encoding='utf-8').readlines()]
        practice_pairs = []
        for _ in range(self.config.numSessions):
            words = practice_words[:]
            random.shuffle(words)
            these_pairs = []
            for __ in range(self.config.nPairs):
                these_pairs.append((words.pop(), words.pop()))
            practice_pairs.append(these_pairs)
        return practice_pairs

    def _prepare_all_sessions_lists(self):
        """
        Prepares word lists for all sessions
        :return: (pairs, cue_dirs, stim_lists, test_order)
        """
        self._assert_good_list_params()
        self._verify_files()

        pairs_by_session = []
        cue_dirs_by_session = []
        stim_lists_by_session = []
        test_order_by_session = []

        for _ in range(self.config.nTrials):
            pairs, cue_dirs, test_order, list_is_stim = \
                self._prepare_single_session_lists()
            pairs_by_session.append(pairs)
            cue_dirs_by_session.append(cue_dirs)
            stim_lists_by_session.append(list_is_stim)
            test_order_by_session.append(test_order)

        return pairs_by_session, cue_dirs_by_session, stim_lists_by_session, test_order_by_session

    def _make_latex_preamble(self):
        """
        Makes the preamble for the LaTeX document
        :return: a list with the preamble
        """
        preamble = [
            '\\documentclass{article}',
            '\\usepackage[margin=1in]{geometry}',
            '\\usepackage{multirow}',
            '\\usepackage{tabularx}',
            '\\begin{document}',
            '\\begin{center}',
            '{\\large %s RAM\\_%s word lists}' %
            (self.subject.replace('_', '\\_'), self.config.EXPERIMENT_NAME),
            '\\end{center}',
            ''
        ]
        return preamble

    def make_stim_forms(self):
        """
        Make the sheets stating which stim type to use per list
        """
        exp = self.exp
        state = self.exp.restoreState()
        config = self.config
        print 'making stim sheets'
        subj = exp.getOptions().get('subject')
        # Loop over sessions
        for session_i in range(config.nSessions):
            exp.setSession(session_i)
            form_name = '%s_%s_s%d_wordlists' % (subj, self.experiment_name, session_i)
            stim_form = exp.session.createFile(form_name+'.tex')

            # Sets up the initial part of the LaTeX document
            preamble = [
                '\\documentclass{article}',
                '\\usepackage[margin=1in]{geometry}',
                '\\usepackage{multirow}',
                '\\usepackage{tabularx}',
                '\\begin{document}',
                '\\begin{center}',
                '{\\large '+subj.replace('_', '\\_')+' RAM %s word lists}\\\\' % self.experiment_name,
                '\\emph{N}: No stimulation; \\emph{R}: Recall; \\emph{E}: Encoding',
                '\\end{center}',
                '']
            document = []

            # trial_stimFirst = None  # state.stimFirst[session_i] TODO: STIMULATION
            # trial_stimType = None  # state.stimType[session_i]
            trial_pairs = state.sessionPairs[session_i]

            already_page_broke = False

            #  last_stimType = None
            # Loop over trials
            #  stimTypes_seen = 0
            for trial_i in range(config.nTrials):
                this_stim_type = 'none'  # trial_stimType[trial_i]

                # block header
                if trial_i >= 15 and not already_page_broke:
                    already_page_broke = True
                    document.append('\\pagebreak')
                    document.append('\\begin{center}')
                    document.append('{\\large '+subj.replace('_', '\\_')+' RAM\\_PAL word lists}\\\\')
                    document.append('\\emph{N}: No stimulation; \\emph{R}: Recall; \\emph{E}: Encoding')
                    document.append('\\end{center}')
                    document.append('\\vspace{.1in}\n')

                this_pairs = trial_pairs[trial_i]
                this_stim_first = False  # trial_stimFirst[trial_i]
                # insert vertical space
                document.append('\\vspace{.1in}')

                # Wordlist items are centered
                centers = 'c '*(len(this_pairs))
                document.append('\\hspace{.5in}\\begin{tabular}{r||'+centers+'}')
                rowline1 = '\\multirow{2}{*}{List %d%s : \\emph{%s}} & ' % \
                           (trial_i+1, '' if trial_i+1 >= 10 else '~~', this_stim_type[0].upper())
                for i in range(len(this_pairs)):
                    word = this_pairs[i][0]
                    bold_word = '\\textbf{%s}' % \
                                word if this_stim_first ^ i % 2 != 0 and this_stim_type != 'none' and config.doStim \
                                else word
                    rowline1 += (' & ' if i != 0 else '') + bold_word.encode('utf-8')
                rowline1 += '\\\\'
                document.append(rowline1)
                rowline2 = '\\cline{2-7}\t\t\t& '
                for i in range(len(this_pairs)):
                    word = this_pairs[i][1]
                    bold_word = '\\textbf{%s}' % \
                                word if this_stim_first ^ i % 2 != 0 and this_stim_type != 'none' and config.doStim \
                                else word
                    rowline2 += (' & ' if i != 0 else '') + bold_word.encode('utf-8')
                rowline2 += '\\\\'
                document.append(rowline2)
                document.append('\\end{tabular}')
                document.append('')

            postamble = ['\\end{document}']

            stim_form.write('\n'.join(preamble)+'\n'+'\n'.join(document)+'\n'+'\n'.join(postamble))

            stim_form.close()

            # Make the dvi document
            os.system('cd %s; latex %s >> latexLog.txt' % (os.path.dirname(stim_form.name), stim_form.name))
            # Convert the dvi to pdf
            dvi_form = exp.session.createFile(form_name+'.dvi')
            dvi_form.close()
            os.system('cd %s; dvipdf %s >> latexLog.txt' % (os.path.dirname(dvi_form.name), dvi_form.name))

            # Clean up unneccesary files
            os.system('cd %s; rm %s.dvi; rm %s.log; rm %s.aux' % (os.path.dirname(dvi_form.name),
                      form_name, form_name, form_name))

        exp.setSession(0)

    def _show_making_stim_forms(self):
        self.video.clear('black')
        self.video.showCentered(Text('Making word list files.\nThis may take a moment...'))
        self.video.updateScreen()

    def is_session_started(self):
        """
        :return: True if this session has previously been started
        """
        state = self.exp.restoreState()
        return state.session_started

    def is_experiment_started(self):
        """
        :return: True if experiment has previously been started
        """
        state = self.exp.restoreState()
        if state:
            return True
        else:
            return False

    def _write_lst_files(self, session_lists, practice_pairs):
        """
        Writes .lst files to the session folders
        :param session_lists: word lists for each list for each session
        """
        for session_i, (sess_pairs, these_practice_pairs) in enumerate(zip(session_lists, practice_pairs)):
            # Set the session so it writes the files in the correct place
            self.exp.setSession(session_i)
            for pair_i in range(self.config.nPairs):
                self._write_single_lst_file(these_practice_pairs, 'p_%d.lst' % pair_i)
            for list_i, pairs in enumerate(sess_pairs):
                for pair_i in range(self.config.nPairs):
                    self._write_single_lst_file(pairs, '%d_%d.lst' % (list_i, pair_i))

    def _write_single_lst_file(self, pairs, label):
        """
        Writes a single .lst file to the current session folder
        :param pairs: word list for that specific trial
        :param label: name of the file to be written in the session folder
        """
        list_file = self.exp.session.createFile(label)
        for pair in pairs:
            list_file.write('\n'.join([Utils.remove_accents(word) for word in pair]))
            list_file.write('\n')
        list_file.close()

    def init_experiment(self):
        """
        Initializes the experiment, sets up the state so that lists can be run
        :return: state object
        """

        if self.is_experiment_started():
            raise Exception('Cannot prepare trials with an in progress session!')

        Utils.seed_rng(self.exp.getOptions().get('subject'))

        self._copy_word_pool()

        # Notify the user that we're preparing the trials
        # TODO: MOVE TO VIEW
        if self.video:
            self._show_prepare_message()

        # Make the word lists
        (session_pairs, session_cue_dirs, session_stim, session_test_order) = self._prepare_all_sessions_lists()
        practice_pairs = self._prepare_practice_lists()

        # Write out the .lst files
        self._write_lst_files(session_pairs, practice_pairs)

        # Save out the state
        state = self.exp.restoreState()
        self.exp.saveState(state,
                           session_started=False,
                           trialNum=0,
                           practiceDone=False,
                           sessionPairs=session_pairs,
                           sessionCueDirs=session_cue_dirs,
                           sessionTestOrder=session_test_order,
                           practicePairs=practice_pairs,
                           sessionStim=session_stim,
                           lastStimTime=0,
                           sessionNum=0,
                           language='spanish' if self.config.LANGUAGE == 'SP' else 'english',
                           LANG=self.config.LANGUAGE)

        #self._show_making_stim_forms()
        #self.make_stim_forms()

        self.exp.setSession(0)
        return self.exp.restoreState()

    def get_stim_type(self):
        """
        Gets the type of stimulation for the given session
        :return: type of stimulation
        """
        return 'NO_RECORD' if self.config.experiment == 'PAL0' else\
               'NO_STIM' if self.config.experiment == 'PAL1' else\
               'OPEN_STIM' if self.config.experiment == 'PAL2' else\
               'CLOSED_STIM' if self.config.experiment == 'PAL3' else\
               'UNKNOWN'

    def _make_session_lists(self):
        """
        Makes all of the lists of pairs for a given session
        :return: (pres_pairs, cue_dir, test_order)
        """
        wordpool = CustomTextPool(self.config.wp)
        random.shuffle(wordpool)

        pairs_per_session = self.config.nPairs*self.config.nTrials
        unused_cue_dirs = [0, 1]*(pairs_per_session/2)
        random.shuffle(unused_cue_dirs)

        pres_pairs = []
        cue_dirs = []
        test_orders = []
        for list_i in range(self.config.nTrials):
            test_orders.append(self.make_test_order())

            cue_dirs.append(unused_cue_dirs[:self.config.nPairs])
            del unused_cue_dirs[:self.config.nPairs]

            these_pairs = []
            for pair_i in range(self.config.nPairs):
                these_pairs.append((wordpool.pop().name, wordpool.pop().name))
            pres_pairs.append(these_pairs)

        return pres_pairs, cue_dirs, test_orders

    def make_test_order(self):
        evens = range(0, self.config.nPairs, 2)
        odds = range(1, self.config.nPairs, 2)
        random.shuffle(odds)
        random.shuffle(evens)
        order = []
        for i in range(self.config.nPairs):
            order.append(evens.pop() if i % 2 == 0 else odds.pop())
        return order


class PALExperimentRunner:

    def __init__(self, fr_experiment, clock, log, mathlog, video, audio, callbacks):
        self.fr_experiment = fr_experiment
        self.config = fr_experiment.config
        self.clock = clock
        self.log = log
        self.mathlog = mathlog
        self.video = video
        self.audio = audio
        self.callbacks = callbacks
        self._on_screen = True
        self.start_beep = CustomBeep(self.config.startBeepFreq,
                             self.config.startBeepDur,
                             self.config.startBeepRiseFall)

    def log_message(self, message, time=None):
        """
        Logs a message to the sessionLog file
        :param message: the message to be logged
        :param time: (optional) the time to log with the message
        """
        if not time:
            time = self.clock
        if isinstance(message, unicode):
            message = unicodedata.normalize('NFKD', message).encode('ascii', 'ignore')
        self.log.logMessage(message, time)

    @staticmethod
    def choose_yes_or_no(message):
        """
        Presents "message" to user
        :param message: message to present to user
        :return: True if user pressed Y, False if N
        """
        bc = ButtonChooser(Key('Y'), Key('N'))
        (_, button, _) = Text(message).present(bc=bc)
        return button == Key('Y')

    def _check_should_run_practice(self, state):
        """
        Checks if practice should be skipped
        :param state:
        :return:True if practice list should be run again
        """
        if state.practiceDone:
            return self.choose_yes_or_no(
                'Practice list already ran.\nPress Y to run again\nPress N to skip'
            )
        else:
            return True

    def _check_sess_num(self, state):
        """
        Prompts the user to check the session number
        :return: True if verified, False otherwise
        """
        subj = self.fr_experiment.subject
        return self.choose_yes_or_no(
            'Running %s in session %d of %s\n(%s).\n Press Y to continue, N to quit' %
            (subj,
             state.sessionNum + 1,
             self.config.experiment,
             state.language))

    def _send_state_message(self, state, value, meta=None):
        """
        Sends message with STATE information to control pc
        :param state: 'PRACTICE', 'ENCODING', 'WORD'...
        :param value: True/False
        """
        if state not in self.config.state_list:
            raise Exception('Improper state %s not in list of states' % state)
        self._send_event('STATE', state=state, value=value, meta=meta)

    def _send_trial_message(self, trial_num):
        """
        Sends message with TRIAL information to control pc
        :param trial_num: 1, 2, ...
        """
        self._send_event('TRIAL', trial=trial_num)

    def _send_sync_np(self, n_syncs=1, delay=0, jitter=0):
        for _ in range(n_syncs):
            self._send_event('SYNCNP')
            self.clock.delay(delay, jitter)
            self.clock.wait()

    def _send_event(self, *args):
        """
        Sends an arbitrary event
        :param args: Inputs to RAMControl.sendEvent()
        """
        if 'timestamp' not in kwargs:
            kwargs['timestamp'] = timing.now()

        if self.config.control_pc:
            ram_control.send(ram_control.build_message(type, *args, **kwargs))

    def _show_message_from_file(self, filename):
        """
        Opens a file with utf-8 encoding, displays the message, waits for any key
        :param filename: file to be read
        """
        waitForAnyKeyWithCallback(self.clock, Text(codecs.open(filename, encoding='utf-8').read()),
                                  onscreenCallback=lambda: self._send_state_message('INSTRUCT', True),
                                  offscreenCallback=lambda: self._send_state_message('INSTRUCT', False))

    def _add_update_callback(self, callback):
        self._update_callback = callback
        self.video.addUpdateCallback(self._update_callback)
        self._cbref = self.video.update_callbacks[-1]

    def _remove_update_callback(self):
        self.video.removeUpdateCallback(self._cbref)

    def _run_practice_list(self, state):
        """
        Runs a practice list
        :param state: state object
        """
        # Retrieve the list from the state object
        practice_list = state.practicePairs[state.sessionNum]

        # Run the list
        self._send_state_message('PRACTICE', True)
        self.clock.tare()
        self.log_message('PRACTICE_TRIAL')
        self._run_list(practice_list, is_practice=True)
        self._send_state_message('PRACTICE', False)

        # Log in state that list has been run
        state.practiceDone = True
        self.fr_experiment.exp.saveState(state)

        # Show a message afterwards
        self._show_message_from_file(self.config.post_practiceList)

    def play_whole_movie(self, movie_file):
        """
        :param movie_file: path to the movie file to play
        Plays any movie file, centered on the screen.
        """
        movie_object = Movie(movie_file)
        movie_shown = self.video.showCentered(movie_object)
        self.video.playMovie(movie_object)
        self.clock.delay(movie_object.getTotalTime())
        self.clock.wait()
        self.video.stopMovie(movie_object)
        self.video.unshow(movie_shown)

    def _countdown(self):
        """
        Shows the 'countdown' video, centered.
        """
        self.video.clear('black')
        self._send_state_message('COUNTDOWN', True)
        self.log_message('COUNTDOWN_START')
        self.play_whole_movie(self.config.countdownMovie)
        self._send_state_message('COUNTDOWN', False)
        self.log_message('COUNTDOWN_END')

    def _on_orient_update(self, *_):
        if self._on_screen:
            self._send_state_message('ORIENT', True)
        else:
            self._send_state_message('ORIENT', False)
        self._on_screen = not self._on_screen

    def _run_list(self, pair_list, cue_dirs=None, rec_order=None, state=None, is_stim=False, is_practice=False):
        """
        runs a single list of the experiment, presenting all of the words
        in word_list, and logging them as <list_type>_WORD
        :param pair_list: words to present
        :param is_stim: whether this list is a stim list
        :param is_practice: (optional) assumes False. True if on practice list
        """

        if (not state or not cue_dirs or not rec_order) and not is_practice:
            raise Exception('State, cue_dir, or rec_order not provided on non-practice list')

        if not self.config.fastConfig:
            if not is_practice:
                self._send_trial_message(state.trialNum + 1)
                trial_label = 'trial #%d' % (state.trialNum + 1)
            else:
                self._send_trial_message(-1)
                trial_label = 'practice trial'

            timestamp = waitForAnyKeyWithCallback(self.clock,
                                                  Text('Press any key for %s' % trial_label),
                                                  onscreenCallback=lambda: self._send_state_message('WAITING', True),
                                                  offscreenCallback=lambda: self._send_state_message('WAITING', False))
        else:
            timestamp = self.clock
            if is_practice:
                self._send_trial_message(-1)

        if not is_practice:
            self.log_message('TRIAL\t%d\t%s' %
                             (state.trialNum + 1, 'STIM' if is_stim else 'NONSTIM'), timestamp)

        # Need a synchronization close to the start of the list
        self._resynchronize(False)

        # Countdown to start...
        self._countdown()

        self.clock.tare()
        encoding_state = 'NON-STIM ENCODING' if not is_stim else 'STIM ENCODING'
        self._send_state_message(encoding_state, True)
        self.log_message('ENCODING_START')
        # ENCODING
        for pair_i, pair in enumerate(pair_list):
            self._present_pair(pair, pair_i, is_stim, is_practice, state.trialNum if state else None)

        self.clock.tare()
        self._send_state_message(encoding_state, False)
        self.log_message('ENCODING_END')

        if self.config.doMathDistract and \
                not self.config.continuousDistract and \
                not self.config.fastConfig:
            self._do_distractor()

        self._run_recall(pair_list, cue_dirs, rec_order, is_practice, state)

    def _run_recall(self, pair_list, cue_dirs, rec_order,  is_practice=False, state=None,):
        """
        Runs the recall period of a word list
        :param state: State object
        :param is_practice: True if list is practice list
        """

        self.clock.tare()
        self._send_state_message('RETRIEVAL', True)
        self.log_message('RECALL_START')
        if is_practice:
            cue_dirs = [i%2 for i in range(len(pair_list))]
            random.shuffle(cue_dirs)
            rec_order = self.fr_experiment.make_test_order()
        elif not state:
            raise Exception('State not provided on practice list')
    
        start_shown = self.video.showCentered(Text(self.config.retrieval_start_text, size=self.config.wordHeight))
        self.video.updateScreen(self.clock)
        self.start_beep.present(self.clock)
        self.video.unshow(start_shown)
        self.video.updateScreen(self.clock)

        for i, (pair_i, cue_dir) in enumerate(zip(rec_order, cue_dirs)):
            pair = pair_list[pair_i]
            probe = pair[cue_dir]
            expecting = pair[(cue_dir + 1) % 2]

            #self._orient(self.config.retrieval_orient_text,
            #             self.config.cue_orientation,
            #             'RETRIEVAL_' if not is_practice else 'PRACTICE_RETRIEVAL_')
            # NO ORIENT IN RETRIEVAL ANYMORE

            self.clock.delay(self.config.cue_orientation + self.config.pre_cue, jitter=self.config.pre_cue_jitter)
            self.clock.wait()

            probe_handle = self.video.showCentered(Text(probe, size=self.config.wordHeight))

            self._add_update_callback(self._on_word_update)
            timestamp = self.video.updateScreen(self.clock)

            label = str(state.trialNum) if not is_practice else 'p'

            self.log_message('TEST_PROBE\t%d\tSP_%d\tTRIAL_%s\tPROBE_%s\tEXPECTING_%s\tDIRECTION_%d' %
                             (i, pair_i, label, probe, expecting, cue_dir), timestamp)

            filename = '%s_%d' % (label, i)
            (_, timestamp) = self.audio.startRecording(filename, t=self.clock)
            self.log_message('REC_START', timestamp)
            self.clock.delay(self.config.cue_duration)
            self.video.unshow(probe_handle)
            timestamp = self.video.updateScreen(self.clock)
            self.log_message('PROBE_OFF', timestamp)
            self._remove_update_callback()

            self.clock.delay(self.config.post_cue)
            self.clock.wait()
            (_, timestamp) = self.audio.stopRecording(self.clock)
            self.log_message('REC_END', timestamp)
        self.clock.tare()
        self._send_state_message('RETRIEVAL', False)
        self.log_message('RECALL_END')

    def _on_word_update(self, *_):
        self._send_state_message('WORD', self._on_screen)
        self._on_screen = not self._on_screen

    def _orient(self, text, duration, list_type):

        self._add_update_callback(self._on_orient_update)
        timestamp_on, timestamp_off = flashStimulusWithOffscreenTimestamp(Text(text, size=self.config.wordHeight),
                                                                          clk=self.clock,
                                                                          duration=duration)
        self._remove_update_callback()
        self.log_message('%sORIENT' % list_type, timestamp_on)
        self.log_message('%sORIENT_OFF' % list_type, timestamp_off)
        self.video.clear('black')
        self.video.updateScreen()

    def _present_pair(self, pair, pair_i, is_stim=False, is_practice=False, list_num=None):
        """
        Presents a single word to the subject
        :param pair: the wordpool object of the word to present
        :param pair_i: the serial position of the word in the list
        :param is_stim: Whether or not this is a (potentially) stimulated word
        :param is_practice: Whether this is a practice list
        """

        self._orient(self.config.encoding_orient_text, self.config.encoding_orientation,
                     'STUDY_' if not is_practice else 'PRACTICE_')

        # Get the text to present
        word_text = CustomText('\n\n'.join(pair), size=self.config.wordHeight)

        # Delay for a moment
        self.clock.delay(self.config.pre_encoding_delay, self.config.pre_encoding_jitter)
        self.clock.wait()

        # Present the word
        timestamp_on, timestamp_off = word_text.presentWithCallback(clk=self.clock,
                                                                    duration=self.config.encoding_duration,
                                                                    updateCallback=self._on_word_update)
        # Log that we showed the word
        ram_control.send(WordMessage('{}-{}'.format(pair[0], pair[1])))
        if not is_practice:
            self.log_message(u'STUDY_PAIR\t%d\tTRIAL_%s\tWORD1_%s\tWORD2_%s\t%s' %
                             (pair_i, list_num,
                              pair[0], pair[1],
                              'STIM' if is_stim else 'NO_STIM'), timestamp_on)
            self.log_message(u'PAIR_OFF', timestamp_off)
        else:
            self.log_message(u'PRACTICE_PAIR\t%d\tWORD1_%s\tWORD2_%s' %
                             (pair_i,
                              pair[0], pair[1]
                              ), timestamp_on)
            self.log_message(u'PRACTICE_PAIR_OFF', timestamp_off)

        self.clock.delay(self.config.post_cue)
        self.clock.wait()
        if self.config.continuousDistract:
            self._do_distractor()

    def _do_distractor(self):
        """
        Presents the subject with a single distractor period
        """

        self._send_state_message('DISTRACT', True)
        self.log_message('DISTRACT_START')

        customMathDistract(clk=self.clock,
                           mathlog=self.mathlog,
                           numVars=self.config.MATH_numVars,
                           maxProbs=self.config.MATH_maxProbs,
                           plusAndMinus=self.config.MATH_plusAndMinus,
                           minDuration=self.config.MATH_minDuration,
                           textSize=self.config.MATH_textSize,
                           callback=ram_control.send_math_message)

        self._send_state_message('DISTRACT', False)
        self.log_message('DISTRACT_END')

    def should_skip_session(self, state):
        """
        Check if session should be skipped
        :param state: State of experiment
        :return: True if session is skipped, False otherwise
        """
        if self.fr_experiment.is_session_started():
            bc = ButtonChooser(Key('SPACE') & Key('RETURN'), Key('ESCAPE'))
            self.video.clear('black')
            (_, button, timestamp) = Text(
                'Session %d was previously started\n' % (state.sessionNum + 1) +
                'Press SPACE + RETURN to skip session\n' +
                'Press ESCAPE to continue'
                ).present(self.clock, bc=bc)
            if 'AND' in button.name:
                self.log_message('SESSION_SKIPPED', timestamp)
                state.sessionNum += 1
                state.trialNum = 0
                state.practiceDone = False
                state.session_started = False
                self.fr_experiment.exp.saveState(state)
                waitForAnyKey(self.clock, Text('Session skipped\nRestart RAM_%s to run next session' %
                                               self.config.experiment))
                return True
        return False

    def _resynchronize(self, show_syncing):
        """
        Performs a resynchronization (christian's algorithm)
        (to be run before each list)
        """
        if self.config.control_pc:
            if show_syncing:
                ram_control.align_clocks(callback=self.resync_callback)
            else:
                ram_control.align_clocks()

    def _run_all_lists(self, state):
        """
        Runs all of the lists in the given session, read from state
        :param state: State object
        """
        lists = state.sessionPairs[state.sessionNum]
        is_stims = state.sessionStim[state.sessionNum]
        cue_dirs = state.sessionCueDirs[state.sessionNum]
        test_orders = state.sessionTestOrder[state.sessionNum]
        while state.trialNum < len(lists):
            this_list = lists[state.trialNum]
            is_stim = is_stims[state.trialNum]
            cue_dir = cue_dirs[state.trialNum]
            test_order = test_orders[state.trialNum]
            # Sync with NP 10 more times over 2.5 secs
            self._run_list(this_list, cue_dir, test_order, state, is_stim)
            state.trialNum += 1
            self.fr_experiment.exp.saveState(state)
            self._resynchronize(True)

    def run_session(self, keyboard):
        """
        :param keyboard: KeyTrack instance
        Runs a full session of free recall
        """
        config = self.config
        self.video.clear('black')

        if config.show_video:
            self._send_state_message('INSTRUCT', True)
            self.log_message('INSTRUCT_VIDEO\tON')
            playIntro.playIntro(self.fr_experiment.exp, self.video, self.audio, keyboard, True, config.LANGUAGE)
            self._send_state_message('INSTRUCT', False)
            self.log_message('INSTRUCT_VIDEO\tOFF')
        elif config.show_instruct_text:
            instruct(codecs.open(config.intro_file, 'r', 'utf-8').read())

        # Get the state object
        state = self.fr_experiment.exp.restoreState()

        # Return if out of sessions
        if self.is_out_of_sessions(state):
            return

        # Set the session appropriately for recording files
        self.fr_experiment.exp.setSession(state.sessionNum)

        # Clear the screen
        self.video.clear('black')

        if not self._check_sess_num(state):
            exit(1)

        self.video.clear('black')

        stim_type = self.fr_experiment.get_stim_type()
        stim_session_type = '%s_SESSION' % stim_type
        self.log_message('SESS_START\t%s\t%s\tv_%s' % (
                         state.sessionNum + 1,
                         stim_session_type,
                         str(self.config.VERSION_NUM)))

        # Reset the list number on the control PC to 0
        self._send_trial_message(-1)
        self._send_event('SESSION', session=state.sessionNum + 1, session_type=stim_type)

        self._send_state_message('MIC TEST', True)
        self.log_message('MIC_TEST')
        if not customMicTest(2000, 1.0):
            return
        self._send_state_message('MIC TEST', False)

        if state.trialNum == 0 and self._check_should_run_practice(state):
            self._resynchronize(False)
            self._run_practice_list(state)
            self._resynchronize(True)
            state = self.fr_experiment.exp.restoreState()
        
        self.fr_experiment.exp.saveState(state, session_started=True)
        state = self.fr_experiment.exp.restoreState()

        self._run_all_lists(state)

        self.fr_experiment.exp.saveState(state,
                                         trialNum=0,
                                         session_started=False,
                                         sessionNum=state.sessionNum+1,
                                         practiceDone=False)

        timestamp = waitForAnyKey(self.clock, Text('Thank you!\nYou have completed the session.'))
        self.log_message('SESS_END', timestamp)
        self._send_event('EXIT')

        self.clock.wait()

    @staticmethod
    def is_out_of_sessions(state):
        """
        :param state: experiment state
        :return: true if all sessions have been run, False otherwise
        """
        return state.sessionNum >= len(state.sessionPairs)


def cleanup_ram_control():
    """
    Cleanup anything related to the Control PC
    Close connections, terminate threads.
    """


# noinspection PyShadowingBuiltins
def exit(num):
    """
    :param num: exit code number
    Override sys.exit since Python does not exit until all threads have exited
    """
    try:
        cleanup_ram_control()
    finally:
        sys.exit(num)


def connect_to_control_pc(subject, session, config):
    """
    establish connection to control PC
    """
    if not config.control_pc:
        return
    video = VideoTrack.lastInstance()
    video.clear('black')

    ram_control.configure(config.experiment, config.version, session, config.stim_type, subject, config.state_list)
    clock = PresentationClock()
    if not ram_control.initiate_connection():
        waitForAnyKey(clock,
                      Text("CANNOT SYNC TO CONTROL PC\nCheck connections and restart the experiment",
                           size=.05))
        exit(1)

    cb = lambda: flashStimulus(Text("Waiting for start from control PC..."))
    ram_control.wait_for_start_message(poll_callback=cb)


def run():
    """
    The main function that runs the experiment
    """
    checkVersion(MIN_PYEPL_VERSION)

    # Start PyEPL, parse command line options
    exp = Experiment(use_eeg=False)
    exp.parseArgs()
    exp.setup()

    # Users can quit with escape-F1
    exp.setBreak()
    RAMControl.instance().register_handler("EXIT", exit)
    RAMControl.instance().socket.log_path = exp.session.fullPath()

    # Get config
    config = exp.getConfig()

    if exp.restoreState():
        session_num = exp.restoreState().sessionNum
    else:
        session_num = 0

    # Have to set session before creating tracks
    exp.setSession(session_num)
    subject = exp.getOptions().get('subject')

    # Set up tracks
    video = VideoTrack('video')
    clock = PresentationClock()


    fr_experiment = PALExperiment(exp, config, video, clock)

    if not fr_experiment.is_experiment_started():
        state = fr_experiment.init_experiment()
    else:
        state = exp.restoreState()

    log = LogTrack('session')
    mathlog = LogTrack('math')
    audio = CustomAudioTrack('audio')
    keyboard = KeyTrack('keyboard')

    experiment_runner = PALExperimentRunner(fr_experiment,
                                            clock,
                                            log,
                                            mathlog,
                                            video,
                                            audio,
                                            callbacks)

    if experiment_runner.should_skip_session(state):
        return

    connect_to_control_pc(subject, session, config)

    experiment_runner.run_session(keyboard)


# only do this if the experiment is run as a stand-alone program (not imported as a library)
if __name__ == "__main__":
    run()
