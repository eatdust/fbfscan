import gphoto2 as gp
import os as os
import logging as logging
import sys as sys

class scanner(object):

    def __init__(self,name='',pylog=True, summary=False):

        if pylog:
            gp.use_python_logging(mapping={
                gp.GP_LOG_ERROR   : logging.INFO,
                gp.GP_LOG_DEBUG   : logging.DEBUG,
                gp.GP_LOG_VERBOSE : logging.DEBUG - 3,
                gp.GP_LOG_DATA    : logging.DEBUG - 6})

        self.context = gp.gp_context_new()
        error, self.camera = gp.gp_camera_new()
        if error != 0:
            print('init scanner: cannot allocate ressources!')
            self.error = error
            return

        self.connect()
        error, text = gp.gp_camera_get_summary(self.camera, self.context)
        if error != 0:
            print('init scanner: cannot get camera summary!')
            self.error = error
            return 
        
        self.text = text.text
        if summary:
            print('init summary:')
            print(text.text)
            print('')
            
        error = self.get_config()
        if error !=0:
            print('init scanner: cannot get camera config!')
            self.error = error
            return
        else:
            self.error = 0
            self.get_exposure_bias()
            self.get_exposure_time()
            self.get_iso()

        self.deconnect()
            
            
    def connect(self,success=True):
        error = gp.gp_camera_init(self.camera,self.context)
        if (error !=0):
            print('cannot connect to camera!               ')
            sys.stdout.write("\033[F")
            success = False
            
    def deconnect(self,success=True):
        error = gp.gp_camera_exit(self.camera, self.context)
        if error !=0:
            print('camera not properly deconnect!          ')
            sys.stdout.write("\033[F")
            success = False

    def get_config(self):
        error, config = gp.gp_camera_get_config(self.camera,self.context)
        if error != 0:
            print('init scanner: cannot get camera config!')
        else:
            self.config = config

        return error
            

    def set_config(self, config):
        error = gp.gp_camera_set_config(self.camera,config,self.context)
        if error != 0:
            print('init scanner: cannot set camera config!')
        else:
            self.config = config
                    

    def get_exposure_bias(self):

        error, bias = gp.gp_widget_get_child_by_name(self.config,'exposurecompensation')

        if error !=0:
            print(error)
            print('get_exposure_bias: cannot read widget!')
            return
        else:
            self.bias = bias

        error, value = gp.gp_widget_get_value(bias)

        if error !=0:
            print(error)
            print('get_exposure_bias: cannot read value!')
            return
        
        count = gp.check_result(gp.gp_widget_count_choices(self.bias))
        for choice in range(count):
            error, test = gp.gp_widget_get_choice(self.bias, choice)
            if test == value:
                break

        if error !=0:
            print(error)
            print('get_exposure_bias: cannot find choice!')
            return
        
        return choice, value
            

    def set_exposure_bias(self,choice):

        count = gp.check_result(gp.gp_widget_count_choices(self.bias))
        
        if choice < 0 or choice > count-1:
            print('choice max is:',count)
            print('set_exposure_bias: choice out of range!')
            return

        error, value = gp.gp_widget_get_choice(self.bias, choice)
        
        error = gp.gp_widget_set_value(self.bias,value)        

        if error !=0:
            print('set_exposure_bias: cannot set value!')

        error = gp.gp_camera_set_config(self.camera, self.config, self.context)
         
        if error !=0:
            print('set_exposure_bias: cannot push config!')
         
            
        return value


    def get_exposure_time(self):

        error, exptime = gp.gp_widget_get_child_by_name(self.config,'shutterspeed2')

        if error !=0:
            print(error)
            print('get_exposure_time: cannot read widget!')
            return
        else:
            self.exptime = exptime

        error, value = gp.gp_widget_get_value(exptime)

        if error !=0:
            print(error)
            print('get_exposure_time: cannot read value!')
            return
        
        count = gp.check_result(gp.gp_widget_count_choices(self.exptime))
        for choice in range(count):
            error, test = gp.gp_widget_get_choice(self.exptime, choice)
            if test == value:
                break

        if error !=0:
            print(error)
            print('get_exposure_time: cannot find choice!')
            return
        
        return choice, value
            

    def set_exposure_time(self,choice):

        count = gp.check_result(gp.gp_widget_count_choices(self.exptime))
        
        if choice < 0 or choice > count-1:
            print('choice max is:',count)
            print('set_exposure_time: choice out of range!')
            return

        error, value = gp.gp_widget_get_choice(self.exptime, choice)
        
        error = gp.gp_widget_set_value(self.exptime,value)        

        if error !=0:
            print('set_exposure_exptime: cannot set value!')

        error = gp.gp_camera_set_config(self.camera, self.config, self.context)
         
        if error !=0:
            print('set_exposure_exptime: cannot push config!')
         
            
        return value


    def get_iso(self):

        error, isovalue = gp.gp_widget_get_child_by_name(self.config,'iso')

        if error !=0:
            print(error)
            print('get_iso: cannot read widget!')
            return
        else:
            self.iso = isovalue

        error, value = gp.gp_widget_get_value(isovalue)

        if error !=0:
            print(error)
            print('get_iso: cannot read value!')
            return
        
        count = gp.check_result(gp.gp_widget_count_choices(self.iso))
        for choice in range(count):
            error, test = gp.gp_widget_get_choice(self.iso, choice)
            if test == value:
                break

        if error !=0:
            print(error)
            print('get_iso: cannot find choice!')
            return
        
        return choice, value
            

    def set_iso(self,choice):

        count = gp.check_result(gp.gp_widget_count_choices(self.iso))
        
        if choice < 0 or choice > count-1:
            print('choice max is:',count)
            print('set_iso: choice out of range!')
            return

        error, value = gp.gp_widget_get_choice(self.iso, choice)
        
        error = gp.gp_widget_set_value(self.iso,value)        

        if error !=0:
            print('set_iso: cannot set value!')

        error = gp.gp_camera_set_config(self.camera, self.config, self.context)
         
        if error !=0:
            print('set_iso: cannot push config!')
         
            
        return value



    

    def single_capture(self,path,filename,success=True):
        
        error, swigpath = gp.gp_camera_capture(self.camera,gp.GP_CAPTURE_IMAGE,self.context)
        if error !=0:
            print('single_capture: error in capturing image')
            sys.stdout.write("\033[F")
            success = False            
            
        target = os.path.join(path,filename)


        error, camfile = gp.gp_camera_file_get(self.camera, swigpath.folder, swigpath.name,
                                               gp.GP_FILE_TYPE_NORMAL, self.context)

        error = gp.gp_file_save(camfile,target)

        if error !=0:
            print('single_capture: error in getting/saving image')
            sys.stdout.write("\033[F")
            success = False
    
