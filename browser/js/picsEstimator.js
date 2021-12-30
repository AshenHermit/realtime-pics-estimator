class PicsEstimatorScript extends Script{
    constructor(){
        super()
        self.image_urls = []
    }
    async estimatePictures(){
        this.images = Array.from(document.getElementsByTagName("img"))
        var urls = this.images.filter(x=>!!x.src).map(x=>x.src)
        this.py.estimate_images_with_callback(urls)
    }
    async onImageEstimated(url, estimation){
        if(!this.images) return
        var img = this.images.find(x=>x.src==url)

        img.style.outline = "5px #e8612a solid"
        img.style.outlineOffset = "-5px"
        
        var opacity = 0
        if(estimation!=null){
            opacity = Math.max(0.01, Math.min(estimation*1.5-0.2, 1))
        }else{
            opacity = 0
        }
        img.style.opacity = ""+opacity
        img.style.transform = `scale(${opacity})`
    }
}