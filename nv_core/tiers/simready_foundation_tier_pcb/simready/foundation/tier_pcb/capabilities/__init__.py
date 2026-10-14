# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Import hub for the PCB tier's validator modules.

Importing this package imports every validator module in the tier; their
``@register_rule`` / ``@register_requirements`` decorators register the tier's
rules and requirements with ``usd_validation_nvidia``.
"""

from .pcb_aoi.board_geometry import validation
from .pcb_aoi.component_geometry import validation
from .pcb_aoi.component_identity import validation
from .pcb_aoi.usd_organization import validation
