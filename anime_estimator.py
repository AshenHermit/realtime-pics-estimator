from math import ceil, e, floor
from pathlib import Path
from typing import List, Union

from PIL.Image import fromarray
from numpy import lib
from images.gatherer import AnimePicsGatherer, ImagesGatherer, ListOfUrlsGatherer, Rule34Gatherer
from images.image import ImageFormatter

from images.library import ImagesLibrary, save_rule34_bad_drawings
from net.estimator import EstimatorNet, ImagesDataset, ImagesLibPart, NetConfig

import matplotlib.pyplot as plt

import PIL.Image

CWD = Path(__file__).parent.resolve()

class LibrariesGatherer():
    def __init__(self, shuffle_dataset=True) -> None:
        self.libraries:list[ImagesLibrary] = []
        self.elements_total = 0

        self.dataset_maker = ImagesDataset(shuffle_dataset)
    
    def load_library(self, filepath:Path, gatherer:Union[ImagesGatherer, List[ImagesGatherer]], formatter:ImageFormatter=None, estimation=0):
        spath = filepath.relative_to(CWD)
        if len([lib for lib in self.libraries if lib.filepath==filepath])!=0:
            print(f"library of images \"{spath}\" already loaded")
            return

        library = ImagesLibrary(filepath)
        if filepath.exists():
            library.load()
        else:
            library.add_with_gatherer(gatherer, formatter)
            library.save()
        print(f"{library} is ready.")

        self.dataset_maker.add_library(library, estimation)
        self.elements_total += len(library.images)
        self.dataset_maker.elements_total = self.elements_total

        self.libraries.append(library)
    
    def make_dataset(self):
        dataset = self.dataset_maker.make_dataset()
        return dataset

class AnimePicEstimator():
    def __init__(self) -> None:
        self.__estimator:EstimatorNet = None
        self.libs_gatherer = LibrariesGatherer()
        self.validation_libs_gatherer = LibrariesGatherer(False)
        self.model_save_path = CWD/"data/estimator_save"
        self.train_plot_path = CWD/"data/train_plot.png"

        self.good_n = 1.0
        self.bad_n = -1.0

    @property
    def estimator(self):
        if self.__estimator is None:
            valid_dat = self.validation_libs_gatherer.make_dataset()
            self.__estimator = EstimatorNet(self.model_save_path, valid_dat)
        return self.__estimator

    def load_bad_drawings(self):
        artists = ["chubby", "jaeh anthro", "a-", "zeglo-official", "sawacoe", "najimi-sensei", "themarvelousfan", "arkanoego", "nexus", "jcache", "artizek", "octoboy", "bluestrikerbomber comic", "cowboy_bebop comic"]
        gatherers = []
        for artist in artists:
            gth = Rule34Gatherer(max_count=1000, tags=artist, print_progress=True)
            gatherers.append(gth)
            
        self.libs_gatherer.load_library(
            CWD / "data/bad_rule34.dat.gz",
            gatherers,
            self.formatter,
            self.bad_n)
        
    def load_good_drawings(self):
        self.libs_gatherer.load_library(
            CWD / "data/anime_pics.dat.gz",
            AnimePicsGatherer(max_count=-1, test_cookie="8ae029db345ca3b89ca44d9d0bed3bdb", print_progress=True),
            self.formatter,
            self.good_n)

    def load_validation_data(self):
        validation_data = [
            ["https://sitenable.co/o.php?b=4&f=norefer&pv=0&mobile=&u=https%3A%2F%2Fwimg.rule34.xxx%2F%2Fimages%2F4822%2F3b0085581eaa1778608a7b88e7617a6624ba9cb3.jpg%3F5490215",
            self.bad_n],
            ["https://sitenable.co/o.php?b=4&f=norefer&pv=0&mobile=&u=https%3A%2F%2Fwimg.rule34.xxx%2F%2Fimages%2F949%2F2fddfdb2dac61c6336e3bdad87868aba5291c9a9.jpg%3F948879",
            self.bad_n],
            ["https://sitenable.ch/o.php?b=4&f=norefer&pv=0&mobile=&u=https%3A%2F%2Fwimg.rule34.xxx%2F%2Fimages%2F912%2F5734c46955a600779cf3da8de574d3a64c67f756.png%3F911685",
            self.bad_n],
            ["https://sitenable.info/o.php?b=4&pv=2&mobile=&u=https%3A%2F%2Frule34.xxx%2F%2Fsamples%2F4830%2Fsample_9a737f8bc2b1b5804859ffbf4c4d0016.jpg%3F5498189",
            self.bad_n],
            ["https://sitenable.info/o.php?b=4&pv=3&mobile=&u=https%3A%2F%2Frule34.xxx%2F%2Fsamples%2F4829%2Fsample_4f1b271a89645a3d05e026225c48823385f71617.jpg%3F5497956",
            self.bad_n],
            ["https://sitenable.info/o.php?b=4&pv=3&mobile=&u=https%3A%2F%2Fwimg.rule34.xxx%2F%2Fimages%2F4829%2F52e932be5e82ea8a7618b7fe37d10638.jpeg%3F5497943",
            self.bad_n],
            ["https://sitenable.info/o.php?b=4&pv=3&mobile=&u=https%3A%2F%2Frule34.xxx%2F%2Fsamples%2F4829%2Fsample_adf68008a8ea747020c18cf863291683.jpg%3F5497921",
            self.bad_n],
            ["https://sitenable.info/o.php?b=4&pv=3&mobile=&u=https%3A%2F%2Frule34.xxx%2F%2Fsamples%2F4829%2Fsample_28af16dae2c441d67385949043af9d5e77a3849f.jpg%3F5497915",
            self.bad_n],
            ["https://freeanimesonline.com/o.php?b=4&pv=2&mobile=&u=https%3A%2F%2Fimg.rule34.xxx%2F%2Fimages%2F4829%2F58b9f5a92c2deaeb03fb53b9e49f61e75ad8bcd6.png%3F5497588",
            self.bad_n],
            ["https://sitenable.pw/o.php?b=4&pv=2&mobile=&u=https%3A%2F%2Frule34.xxx%2F%2Fsamples%2F4829%2Fsample_6f1816cad928d2d87a9332d262407a65.jpg%3F5497607",
            self.bad_n],
            ["https://sitenable.co/o.php?b=4&pv=2&mobile=&u=https%3A%2F%2Frule34.xxx%2F%2Fsamples%2F4829%2Fsample_d787f8d81c1fef44873776297e13ccf5d0b2fe88.jpg%3F5497592",
            self.bad_n],
            ["https://sitenable.ch/scache/cache/9/5/8/9587f92e5f634084d8399ec725e55b0d.jpg",
            self.bad_n],


            ["https://i.pinimg.com/564x/46/07/d4/4607d454b445f7ae99927a452bc485db.jpg", 
            self.good_n],
            ["https://i.pinimg.com/564x/66/57/89/665789fbde578f35d370110e4efc6fef.jpg",
            self.good_n],
            ["https://i.pinimg.com/564x/14/47/5a/14475ac746fa0ba5ae8db06d853ee10e.jpg",
            self.good_n],
            ["https://i.pinimg.com/564x/2a/5d/48/2a5d48d8a907eba0104f718bd9a665ce.jpg",
            self.good_n],
            ["https://sun9-54.userapi.com/impg/GnJh2Bl2M6SK6gdiWDsUyKD-9Lm7PR-4kWQm_w/oS5hD9l2vOs.jpg?size=1320x1020&quality=96&sign=de95b4a2d3ccceeddb7e9b94fd41efcc&type=album",
            self.good_n],
            ["https://sun9-65.userapi.com/impg/2Rh7C0WHMkrG3FArYFUN_8tI_MSybKVhoUngXw/VrMcmx9vzO4.jpg?size=1242x2160&quality=96&sign=968216f7c113c3a5e47ac2f8eb51e3f6&type=album",
            self.good_n],
            ["https://sun9-51.userapi.com/impg/QjTzMoIvdPwSgo13Ltg-GQs80F1BeVpRDzvq-A/gUTK8_GZFmg.jpg?size=1591x2160&quality=96&sign=68c48bb850ce5e9fe5803ad12ee8e7be&type=album",
            self.good_n],
            ["https://sun9-70.userapi.com/impg/zXKRwF3GCNV2LHDn6h-_VFZ19nJEqHps1krGhw/THl8CbJdO08.jpg?size=1020x1320&quality=96&sign=092af6d3523c9b4ab365b2747f2a92ae&type=album",
            self.good_n],
            ["https://sun9-84.userapi.com/impg/S5VY8rnJog7XXvLeeqC3c7Zj4U4Y6CMhQnPD8Q/-g_cO3-utME.jpg?size=1563x2000&quality=96&sign=bab47f9202c3d83f1755b2678ef955f4&type=album",
            self.good_n],
            ["https://sun9-24.userapi.com/impg/aoBcXnWTbKl7WnPfqaPdmLfj3zRSyz7_OaLTdw/867tfvcTjHo.jpg?size=1203x1917&quality=96&sign=11d7d607af1e2790828c9b01040bebaf&type=album",
            self.good_n],
        ]
        urls = [data[0] for data in validation_data]
        labels = [data[1] for data in validation_data]
        self.validation_libs_gatherer.load_library(
            CWD / "data/validation.dat.gz",
            ListOfUrlsGatherer(max_count=-1, urls=urls, print_progress=True),
            self.formatter,
            labels)

    def display_dataset_data(self):
        fig = plt.figure(figsize=(10, 10))
        for images, labels in self.dataset.take(1):
            for i in range(9):
                ax = plt.subplot(3, 3, i + 1)
                plt.imshow(images[i].numpy().astype("uint8"))
                plt.title(str(labels[i].numpy()))
                plt.axis("off")

    def display_prediction(self):
        dataset = self.validation_libs_gatherer.make_dataset()
        fig = plt.figure(figsize=(16, 16))

        images, labels = list(dataset.take(1))[0]

        width = ceil(images.numpy().shape[0]**(1/2))
        for i, img in enumerate(images):
            ax = plt.subplot(width, width, i + 1)
            img = images[i].numpy()
            img_in_batch = img.reshape(tuple([1]+list(img.shape)))
            pred = self.estimator.model(img_in_batch)
            plt.imshow(img.astype("uint8"))
            plt.title(str(pred.numpy()))
            plt.axis("off")

        file = CWD/'data/validation.png'
        plt.savefig(file)
        plt.close(fig)
        print(f"saved images estimation - \"{file}\"")
        
    def load_train_data(self):
        self.formatter = ImageFormatter(width=NetConfig.image_width, height=NetConfig.image_height)
        self.load_good_drawings()
        self.load_bad_drawings()
        self.load_validation_data()
        self.dataset = self.libs_gatherer.make_dataset()

    def train(self, epochs=10):
        self.load_train_data()
        history = self.estimator.train(self.dataset, epochs=epochs)
        self.estimator.save()
        self.estimator.plot_history(history, self.train_plot_path, epochs)

    def estimate(self, image:PIL.Image.Image):
        return self.estimator.estimate(image)

def main():
    pics_estimator = AnimePicEstimator()
    pics_estimator.load_train_data()
    pics_estimator.display_dataset_data()
    # pics_estimator.train(epochs=4)
    pics_estimator.display_prediction()

    # TODO: deploy this on colab and train virtually

if __name__ == '__main__':
    main()