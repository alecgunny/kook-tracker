from app import db


class Updatable:
    def update(self):
        if not self.completed:
            try:
                self._do_update()
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                raise e
        return self.completed

    def _do_update(self):
        raise NotImplementedError()
