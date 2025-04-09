class ImageAnalysis:
    def __init__(self, camera, comms):
        self._obj = []
        self._camera = camera
        self._comms = comms
    
    async def start_async_analysis(self, fps):
        pass
    
    def get_found_obj(self):
        pass
    
    def stop_async_analysis(self):
        pass
    
    def get_current_offset_closest(self, color, type):
        """
        
        return
         (x,y) correct to closest
         h height estimation
        """
        pass
    
    @staticmethod 
    def quality_of_image(image):
        """
        parms:
         image: Image array
         
        return:
         quality: float [0,1]
        """
        pass

