from typing import List

import sqlalchemy as sa
from flask import url_for

from shared import dtutil

from .. import db
from ..db import db as fsa


class Match(fsa.Model):
    __tablename__ = 'match'
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=False)
    format_id = sa.Column(sa.Integer, sa.ForeignKey('format.id'))
    comment = sa.Column(sa.String(200))
    start_time = sa.Column(sa.DateTime)
    end_time = sa.Column(sa.DateTime)

    has_unexpected_third_game = sa.Column(sa.Boolean)
    is_league = sa.Column(sa.Boolean)
    is_tournament = sa.Column(sa.Boolean)

    players = fsa.relationship('User', secondary=db.match_players)
    modules = fsa.relationship('Module', secondary=db.match_modules)
    games = fsa.relationship('Game', backref='match')
    format = fsa.relationship('Format')
    tournament = fsa.relationship('TournamentInfo', backref='match')

    def url(self):
        return url_for('show_match', match_id=self.id)

    def format_name(self):
        return self.format.get_name()

    def host(self):
        return self.players[0]

    def other_players(self):
        return self.players[1:]

    def other_player_names(self):
        return [p.name for p in self.other_players()]

    def set_times(self, start_time: int, end_time: int):
        self.start_time = dtutil.ts2dt(start_time)
        self.end_time = dtutil.ts2dt(end_time)
        db.Commit()

    def display_date(self):
        if self.start_time is None:
            return ""
        else:
            return dtutil.display_date(self.start_time)

class TournamentInfo(fsa.Model):
    __tablename__ = 'match_tournament'
    id = sa.Column(sa.Integer, primary_key=True)
    match_id = sa.Column(sa.Integer, sa.ForeignKey('match.id'), nullable=False)
    tournament_id = sa.Column(sa.Integer, sa.ForeignKey('tournament.id'), nullable=False)
    round_num = sa.Column(sa.Integer)

class Tournament(fsa.Model):
    __tablename__ = 'tournament'
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(length=200), unique=True, index=True)
    active = sa.Column(sa.Boolean)

def create_match(match_id: int, format_name: str, comment: str, modules: List[str], players: List[str]) -> Match:
    format_id = db.get_or_insert_format(format_name).id
    local = Match(id=match_id, format_id=format_id, comment=comment)
    modules = [db.get_or_insert_module(mod) for mod in modules]
    local.modules = modules
    local.players = [db.get_or_insert_user(user) for user in set(players)]
    db.Add(local)
    db.Commit()
    return local

def get_match(match_id: int) -> Match:
    return Match.query.filter_by(id=match_id).one_or_none()

def get_recent_matches(count: int=10) -> List[Match]:
    return Match.query.order_by(Match.id.desc()).paginate(per_page=count)

def get_recent_matches_by_player(name: str) -> List[Match]:
    return Match.query.filter(Match.players.any(db.User.name == name)).order_by(Match.id.desc())

def get_recent_matches_by_format(format_id: int) -> List[Match]:
    return Match.query.filter(Match.format_id == format_id)

def get_tournament(name: str):
    return Tournament.query.filter_by(name=name).one_or_none()

def create_tournament(name: str):
    local = Tournament(name=name, active=True)
    db.Add(local)
    db.Commit()
    return local

def create_tournament_info(match_id: int, tournament_id: int):
    local = TournamentInfo(match_id=match_id, tournament_id=tournament_id)
    db.Add(local)
    db.Commit()
    return local
