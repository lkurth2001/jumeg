#!/usr/bin/env python


'''Class JuMEG_MergeMEEG

Class to merge brainvision eeg data into MEG-fif file

Authors:
         Prank Boers     <f.boers@fz-juelich.de>
         Praveen Sripad  <praveen.sripad@rwth-aachen.de>
License: BSD 3 clause
----------------------------------------------------------------
merge ECG,EGO signals form BrainVision system into MEG-fif file
-> read meg raw fif
-> read bv eeg
-> find start events in raw and bv-eeg
-> lp-filter eeg and meg data
-> downsample eeg merge into meg-fif
-> adjust meg data size
-> save to disk [...eeg-raw.fif]

example via obj:
from jumeg_merge_meeg import JuMEG_MergeMEEG
JMEEG = JuMEG_MergeMEEG()
JMEEG.meg_fname= my_meg_fname.fif
JMEEG.eeg_fname= my_eeg_fname.vhdr
JMEEG.run()

example  via function call
import jumeg_merge_meeg
jumeg_merge_meeg(.meg_fname= my_meg_fname.fif,eeg_fname= my_eeg_fname.vhdr)

---> update 22.12.2016 FB

'''


import os,sys,argparse
import numpy as np
import mne

from jumeg.jumeg_base                   import JuMEG_Base_IO
from jumeg.filter.jumeg_filter          import jumeg_filter


class JuMEG_MergeMEEG(JuMEG_Base_IO):
    def __init__(self,adjust_size=True,save=True):
        '''
        Class JuMEG_MergeMEEG
           -> merge BrainVision ECG/EOG signals into MEG Fif file
           -> finding common onset via startcode in channel <STI 014>
           -> filter data FIR lp butter 200Hz / 400Hz
           -> downsampling eeg data, srate sould be igher than meg e.g. eeg:5kHz meg:1017.25Hz
           -> rename groups and channel names dynamic & automatic !!!
           meg EEG 0001 -> ECG group ecg
           meg EEG 0002 -> EOG_xxx group eog
           meg EEG 0003 -> EOG_xxx group ecg

           input
            adjust= True : ajust raw-obj data size to startcode-onset and last common sample beween MEG and EEG data
            save  = True : save merged raw-obj

            parameter set via obj:

             meg_fname  = None <full file name>
             eeg_fname  = None <eeg brainvision vhdr full file name> with extention <.vhdr>  
             meeg_extention    = ",eeg-raw.fif" output extention

             stim_channel               = 'STI 014'
             startcode                  = 128  start code for common onset in <stim_channel>
             brainvision_response_shift = 256  used for mne.io.read_raw_brainvision

             flags:
              verbose        = False
              do_adjust_size = True
              do_save        = True

             filter option: can be canged via <obj.filter>
              filter.filter_method = "bw"
              filter.filter_type   ='lp'
              filter.fcut1         = None automatic selected  200Hz or 400Hz
              
              
            return:
             raw obj; new meeg file name

        '''

        super(JuMEG_MergeMEEG,self).__init__()

        self.__version__= '2016.12.24.001'

        self.meg_path  = None
        self.meg_name  = None
        self.meg_fname = None
        self.raw       = None

        self.eeg_path   = None
        self.eeg_name   = None
        self.eeg_fname  = None
        self.eeg_raw    = None

        self.meeg_extention =  ",eeg-raw.fif"

        self.brainvision_response_shift = 256 # to mark response bits to higher 16bit in STI channel

        self.meeg_fname = None

       #--- change channel names and group
        self.channel_types = {'EEG 001': u'ecg', 'EEG 002': u'eog', 'EEG 003': u'eog'}
        self.channel_names = {'EEG 001': u'ECG 001', 'EEG 002': u'EOG hor', 'EEG 003': u'EOG ver'}


      #--- filter obj
        self.filter     = jumeg_filter( filter_method="bw",filter_type='lp',fcut1=None,fcut2=None,remove_dcoffset=False,notch=[] )

        self.event_parameter = {'event_id':128, 'and_mask': 255}
        self.events          = {'consecutive': True, 'output': 'step', 'stim_channel': 'STI 014','min_duration': 0.00001, 'shortest_event': 1, 'mask': 0}

        self.verbose        = False
        self.do_adjust_size = adjust_size
        self.do_save        = save

    def ___get_ev_event_id(self):
        return self.event_parameter['event_id']
    def ___set_ev_event_id(self, v):
        self.event_parameter['event_id'] = v
    event_id  = property(___get_ev_event_id, ___set_ev_event_id)
    startcode = property(___get_ev_event_id, ___set_ev_event_id)

    def ___get_ev_stim_channel(self, v):
        return self.events['stim_channel']
    def ___set_ev_stim_channel(self, v):
        self.events['stim_channel'] = str(v)
    stim_channel = property(___get_ev_stim_channel, ___set_ev_stim_channel)

# ---------------------------------------------------------------------------
# --- check_filter_parameter
# ----------------------------------------------------------------------------
    def check_filter_parameter(self):

        if self.raw.info['sfreq'] > self.eeg_raw.info['sfreq']:
           assert "Warning EEG data sampling fequency %4.3f is lower than MEG data %4.3f " % (self.eeg_raw.info['sfreq'], self.raw.info['sfreq'])
           return False
        return self.filter.calc_lowpass_value( self.raw.info['sfreq'] )

#---------------------------------------------------------------------------
# --- apply_filter_meg_eeg
# ----------------------------------------------------------------------------
    def apply_filter_meg_eeg(self,meg_picks=None,eeg_picks=None):
       '''
          inplace filter all meg and eeg data except trigger channel with  lp
        '''
       print "---> Start filter meg data"
      #--- meg
       self.filter.sampling_frequency = self.raw.info['sfreq']
       self.filter.fcut1 = self.check_filter_parameter()
       print " --> filter info: " + self.filter.filter_info
       self.filter.apply_filter(self.raw._data, picks=meg_picks)
      # ---  bv eeg
       print "---> Start filter bv eeg data"
       self.filter.sampling_frequency = self.eeg_raw.info['sfreq']
       print " --> filter info: " + self.filter.filter_info
       self.filter.apply_filter(self.eeg_raw._data, picks=eeg_picks)
       print " --> Done filter data with lp: %4.3f Hz" %( self.filter.fcut1 )

# ---------------------------------------------------------------------------
# --- get_events
# ----------------------------------------------------------------------------
    def get_events(self,raw):
        print " --> call mne find events"

        ev = mne.find_events(raw, **self.events)

        if self.event_parameter['and_mask']:
           ev[:, 1:] = np.bitwise_and(ev[:, 1:], self.event_parameter['and_mask'])
           ev[:, 2:] = np.bitwise_and(ev[:, 2:], self.event_parameter['and_mask'])

        ev_onset  = np.squeeze( ev[np.where( ev[:,2] ),:])  # > 0
        # ev_offset = np.squeeze( ev[np.where( ev[:,1] ),:])
        ev_id_idx = np.squeeze( np.where( np.in1d( ev_onset[:,2],self.startcode )))

        ev_onset = ev_onset[ ev_id_idx,:]

        return np.int64( ev_onset ) #,ev_offset
#---------------------------------------------------------------------------
#--- get_onset
#----------------------------------------------------------------------------
    def get_onset(self,raw):
        return self.get_events(raw)[0]

#---------------------------------------------------------------------------
#--- get_resample_index
#----------------------------------------------------------------------------
    def get_resample_index(self,timepoints_high_srate=None,timepoints_low_srate=None,sfreq_high=None):
        '''
        Downsampling function to resample signal of samp_length from
        higher sampling frequency to lower sampling frequency.

        Parameters
        ----------
        input:
          timepoints_low_srate : np.array of time points with lower  sampling rate less size than the other
          timepoints_high_srate: np.array of time points with higher sampling rate
          sfreq_high           : higher sampling frequency.

        Returns
        -------
        resamp_idx: np.array of index of <timepoints_high_srate> to downsampled high sampled signal.
        '''
        import numpy as np

        eps_limit = round((0.90 / sfreq_high), 3) # distance  beween timepoints high/low
        resamp_idx = np.zeros( timepoints_low_srate.shape[0],dtype=np.int64 )
        j = 0
        idx=0
        for idx in np.arange(timepoints_low_srate.shape[0],dtype=np.int64):
            while (timepoints_low_srate[idx] - timepoints_high_srate[j] ) > eps_limit:
                   j += 1
            resamp_idx[idx] = j
            j += 1

        return resamp_idx

 #----------------------------------------------------------------------------
 #--- run
 #----------------------------------------------------------------------------
    def run(self):

        meg_data  = np.array([])
        meg_times = np.array([])
        eeg_data  = np.array([])

        print "---> Start JuMEG BrainVision Merger"
        print " --> MEG FIF name: " + self.meg_fname
        if (not os.path.isfile( self.meg_fname ) ):
           print "---> ERROR MEG file: no such file: " + self.meg_fname
           return

        print " --> EEG BV  name: " + self.eeg_fname
        if (not os.path.isfile( self.eeg_fname ) ):
           print "---> ERROR EEG file: no such file: " +self.eeg_fname
           return

       #--- load BV eeg
        print"\n " + "-" * 50
        print " --> load EEG BrainVision data: " + self.eeg_fname
        self.eeg_raw,_ = self.get_raw_obj(self.eeg_fname)
       #--- get events & start code
        eeg_onset_tsl = self.get_onset(self.eeg_raw)
       # --- get ECG & EOG picks
        eeg_picks = self.picks.eeg(self.eeg_raw)

       # --- load meg
        print"\n " + "-" * 50
        print " --> load MEG data:             " + self.meg_fname
        self.raw, _   = self.get_raw_obj(self.meg_fname)
       # --- get events & start code
        meg_onset_tsl = self.get_onset(self.raw)
       # --- get MEG & Ref picks
        meg_picks = self.picks.exclude_trigger(self.raw)

       #--- cal tsl onset; common  tsl range
        eeg_onset_time    = self.eeg_raw.times[eeg_onset_tsl]
        eeg_end_time      = self.eeg_raw.times[self.eeg_raw.last_samp]
        eeg_duration_time = self.eeg_raw.times[self.eeg_raw.n_times - eeg_onset_tsl]

        meg_onset_time   = self.raw.times[meg_onset_tsl]
        meg_end_time     = self.raw.times[self.raw.last_samp]
        meg_duration_time= self.raw.times[self.raw.n_times - meg_onset_tsl]

       #--- adjust data length
        if (eeg_duration_time < meg_duration_time):
            delta_time = eeg_duration_time  #  self.eeg_raw.times[self.eeg_raw.last_samp]
        else:
            delta_time = meg_duration_time

        meg_end_tsl = np.int64( self.raw.time_as_index( delta_time ) + meg_onset_tsl )
        if ( meg_end_tsl > self.raw.last_samp ) :
             meg_end_tsl = self.raw.last_samp
             # delta_time  = self.raw.times[meg_end_tsl - meg_onset_tsl]

        meg_times    = np.zeros(meg_end_tsl - meg_onset_tsl + 1)
        meg_times[:] = self.raw.times[ meg_onset_tsl:meg_end_tsl+1 ]
        meg_times   -= meg_times[0] #  start time seq at zero

        eeg_times    = np.zeros(self.eeg_raw.n_times - eeg_onset_tsl)
        eeg_times[:] = self.eeg_raw.times[eeg_onset_tsl:] # copy times
        eeg_times   -= eeg_times[0] #  start time seq at zero

      #--ToDo find index timepoints colse together
      #--- cp index tp form bv to meg-cannels
        eeg_resample_idx = self.get_resample_index(timepoints_high_srate=eeg_times,timepoints_low_srate=meg_times,sfreq_high=self.eeg_raw.info['sfreq'])
        eeg_resample_idx += eeg_onset_tsl

        print"\n " + "-" * 50
        print" --> MEG Time start: %12.3f end: %12.3f delta: %12.3f" % (meg_onset_time, meg_end_time, meg_duration_time)
        print" --> MEG TSL  start: %12.3f end: %12.3f" % (meg_onset_tsl, self.raw.last_samp)
        print" " + "-" * 50
        print" --> EEG Time start: %12.3f end: %12.3f delta: %12.3f" % (eeg_onset_time, eeg_end_time, eeg_duration_time)
        print" --> EEG TSL  start: %12.3f end: %12.3f" % (eeg_onset_tsl, self.eeg_raw.last_samp)
        print" --> EEG use channels : " + ",".join([self.eeg_raw.ch_names[i] for i in eeg_picks])
        print" --> EEG index        : " + str(eeg_picks)
        print" " + "-" * 50
        print" --> resample idx %d" % (eeg_resample_idx.shape[0])

        meg_end_tsl = meg_onset_tsl + eeg_resample_idx.shape[0]

        print" --> used MEG data range [tsl] -> onset: %d offset: %d  delta: %d" % ( meg_onset_tsl, meg_end_tsl, meg_end_tsl - meg_onset_tsl)

       # --- filter meg / eeg data; no trigger
        self.apply_filter_meg_eeg(meg_picks=meg_picks,eeg_picks=eeg_picks)

       #--- downsampe & merge
       #--- ToDo check if EEG channel in raw exist or add channel
        meg_ch_idx = 1
        eeg_idx    = 0

        for ch in ( self.eeg_raw.ch_names ):  # ECG EOG_hor EOG_ver
            if ch.startswith('E'):
               eeg_idx = self.eeg_raw.ch_names.index(ch)
               chname  = "EEG %03d" %(meg_ch_idx)
              #--- copy eeg downsapled data into raw
               self.raw._data[self.raw.ch_names.index(chname), meg_onset_tsl:meg_end_tsl + 1] = self.eeg_raw._data[eeg_idx, eeg_resample_idx]
              #--- rename groups and ch names
               self.raw.set_channel_types( { chname:ch.split('_')[0].lower() } ) # e.g. ecg eog
               self.raw.rename_channels(   { chname:ch.replace('_',' ')      } )
               meg_ch_idx += 1
            eeg_idx+=1

       # --- adjust data size to merged data block -> meg-onset and meg-end tsls
        if self.do_adjust_size:
           self.raw._data = self.raw._data[:, meg_onset_tsl:meg_end_tsl + 1]

       #--- save meeg
        print" " + "-" * 50
        self.meeg_fname = self.get_fif_name(raw=self.raw,extention=self.meeg_extention,update_raw_fname=True)
        print "BVM MEEG name out: "+ self.meeg_fname
        if self.do_save:
           self.apply_save_mne_data(self.raw,fname=self.meeg_fname,overwrite=True)
        print "---> DONE merge BrainVision EEG data to MEG"
        print" " + "-" * 50
        print"\n"

        return self.raw,self.meeg_fname


def __get_args():

    info_global = """
         JuMEG Merge BrainVision EEG data to MEG Data

         ---> porcess fif file for experiment MEG94T
          jumeg_merge_meeg -fmeg  <xyz.fif> -feeg <xyz.vdr>
        """

        # --- parser

    parser = argparse.ArgumentParser(info_global)

   # ---input files
    parser.add_argument("-fmeg", "--meg_fname", help="meg fif  file name with full path", default='None')
    parser.add_argument("-feeg", "--eeg_fname", help="eeg vhdr file name with full path", default='None')
   # ---flags:
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose mode")
    parser.add_argument("-r", "--run", action="store_true", help="!!! EXECUTE & RUN this program !!!")

    return parser.parse_args(), parser

#=========================================================================================
#==== MAIN
#=========================================================================================
def main(argv):

    opt, parser = __get_args()

    JuMEEG = JuMEG_MergeMEEG()
    JuMEEG.meg_fname = opt.meg_fname
    JuMEEG.eeg_fname = opt.eeg_fname
    JuMEEG.verbose   = opt.verbose

    if opt.run:
       JuMEEG.run()



if __name__ == "__main__":
    main(sys.argv)


'''
jumeg_merge_meeg.py -r -fmeg ~/MEGBoers/data/exp/LDAEP/mne/200098/LDAEP02/130415_1526/1/200098_LDAEP02_130415_1526_1_c,rfDC-raw.fif -feeg ~/MEGBoers/data/exp/LDAEP/eeg/LDAEP02/200098_LDAEP02_2.vhdr

'''
