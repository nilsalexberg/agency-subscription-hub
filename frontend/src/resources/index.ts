import type { ResourceConfig } from '@/types/resource'
import { recipientsConfig } from './recipients'
import { splitConfigsConfig } from './split-configs'
import { plansConfig } from './plans'
import { clientsConfig } from './clients'
import { paymentsConfig } from './payments'
import { auditLogsConfig } from './audit-logs'
import { usersConfig } from './users'

export const RESOURCES: ResourceConfig[] = [
  recipientsConfig,
  splitConfigsConfig,
  plansConfig,
  clientsConfig,
  paymentsConfig,
  auditLogsConfig,
  usersConfig,
]
