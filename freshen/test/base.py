#-*- coding: utf8 -*-

import traceback
import sys

from freshen.context import ftc, scc
from freshen.stepregistry import UndefinedStepImpl, AmbiguousStepImpl
from freshen.core import DryStepsRunner


class ExceptionWrapper(Exception):

    def __init__(self, e, step, discard_frames=0):
        e = list(e)
        while discard_frames:
            e[2] = e[2].tb_next
            discard_frames -= 1
        self.e = e
        self.step = step

    def __str__(self):
        return "".join(traceback.format_exception(*self.e))


class FeatureSuite(object):

    _multiprocess_can_split_ = True

    def setUp(self):
        #log.debug("Clearing feature context")
        ftc.clear()


class FreshenTestCase(object):

    start_live_server = True
    database_single_transaction = True
    database_flush = True
    selenium_start = False
    no_database_interaction = False
    make_translations = True
    required_sane_plugins = ["django", "http"]
    django_plugin_started = False
    http_plugin_started = False
    last_step = None

    test_type = "http"

    def __init__(self, step_runner, step_registry, feature, scenario, feature_suite, position, feature_path):
        self.feature = feature
        self.scenario = scenario
        self.context = feature_suite
        self.step_registry = step_registry
        self.step_runner = step_runner
        self.position = position
        self.feature_path = feature_path

        self.description = feature.name + ": " + scenario.name

    def setUp(self):
        #log.debug("Clearing scenario context")
        scc.clear()

    def runAfterStepHooks(self):
        for hook_impl in reversed(self.step_registry.get_hooks('after_step', self.scenario.get_tags())):
            hook_impl.run(self.scenario)

    def runStep(self, step, discard_frames=0):
        try:
            self.last_step = step
            result = self.step_runner.run_step(step)
        except UndefinedStepImpl, e:
            if isinstance(self.step_runner, DryStepsRunner):
                raise
            for hook_impl in self.step_registry.get_hooks('undefined', self.scenario.get_tags()):
                hook_impl.run(self.scenario, e)
            raise
        except AmbiguousStepImpl, e:
            if isinstance(self.step_runner, DryStepsRunner):
                raise
            for hook_impl in self.step_registry.get_hooks('ambiguous', self.scenario.get_tags()):
                hook_impl.run(self.scenario, e)
            raise
        except (AssertionError, ExceptionWrapper):
            raise
        except:
            raise ExceptionWrapper(sys.exc_info(), step, discard_frames)
        self.runAfterStepHooks()
        return result

    def runScenario(self):
        raise NotImplementedError('Must be implemented by subclasses')

    def address(self):
        return self.feature_path, None, self.position
