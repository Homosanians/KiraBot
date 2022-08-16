class MemeProviderResponse:
    def __init__(self, error, image, post_id):
        # no memes left
        self.error = error
        self.image = image
        self.post_id = post_id
