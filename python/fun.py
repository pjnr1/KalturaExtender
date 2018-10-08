from Llab_libs.KalturaExtensions import *
from Llab_libs.statics_helper import load_statics
from Llab_libs.Logger import *


logger = SimpleLogger()

def get_streams():
    client = KalturaExtender()
    cat = load_statics('Llab_libs/kaltura_categoryIds')
    entries = client.getEntries(filters={'categoriesIdsMatchAnd': cat['Recordings']})
    logger.log(string="N: {}".format(len(entries)), color="red")
    for streams in entries.items():
        logger.critical(string="Parent: {} {}".format(streams[1].id, streams[1].name))
        listOfEntries = client.getEntries(filters={'parentEntryIdEqual': streams[0]})
        for entry in listOfEntries.items():
            logger.warning(string="Child:  {} {}".format(entry[1].id, entry[1].name))


if __name__ == '__main__':
    get_streams()
