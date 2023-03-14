import logging

from app import db


class Updatable:
    def update(self):
        if not self.completed:
            try:
                self._do_update()
            except Exception as e:
                logging.error(
                    "Encountered exception while updating {}:\n{}".format(
                        self, str(e)
                    )
                )
                db.session.rollback()
                raise e
            else:
                db.session.commit()
        return self.completed

    def _do_update(self):
        raise NotImplementedError()
