# -*- coding: utf-8 -*-
#Basado en la librería de MEGA para pelisalacarte que programó divadr y modificado por tonikelope para dar soporte a MEGACRYPTER

class ValidationError(Exception):
    """
    Error in validation stage
    """
    pass


class RequestError(Exception):
    """
    Error in API request
    """
    # TODO add error response messages
    pass
