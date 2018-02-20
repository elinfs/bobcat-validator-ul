from azure.storage.blob import BlockBlobService

def main():
    try:
        import config 
    except:
        raise ValueError('Please specify configuration settings in config.py.')
        
    block_blob_service = BlockBlobService(account_name=config.STORAGE_ACCOUNT_NAME, account_key=config.STORAGE_ACCOUNT_KEY)

    generator = block_blob_service.list_blobs(config.STORAGE_CONTAINER)
    for blob in generator:
        print(blob.name)
        block_blob_service.get_blob_to_path(config.STORAGE_CONTAINER, blob.name, config.DYNAMIC_FILES_LOCAL_PATH + blob.name)

if __name__ == "__main__":
    main()