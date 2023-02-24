import tokens
from utils import Logger

def space(space_name: str, space_id: str):
    pass

def action_token(token_name: str, token_id: str) -> bool:
    Logger.log(3, "rollback - removing token")
    token = None

    Logger.log(3, f"rollback - getting token from id {token_id}")
    if token_id:
        token = tokens.getNamedToken(token_id)

    if not token:
        Logger.log(3, f"rollback - id is not correct, getting from name {token_name}")
        response = tokens.getNamedTokenByName(token_name)

        # it is ok, because we do not have to delete token
        if response.status_code == 404:
            Logger.log(3, "rollback - token does not exist on server, everything is OK")
            return True

        token_id = response["id"]

    Logger.log(3, f"rollback - removing token with id {token_id}")
    response = tokens.deleteNamedToken(token_id)
    Logger.log(3, f"rollback - token with id {token_id} removed: {response.ok}")
    return response.ok

