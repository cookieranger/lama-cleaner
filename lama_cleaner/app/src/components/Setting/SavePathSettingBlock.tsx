import React, { ReactNode } from 'react'
import { useRecoilState } from 'recoil'
import { Switch, SwitchThumb } from '../shared/Switch'
import SettingBlock from './SettingBlock'

function SavePathSettingBlock() {
  return (
    <SettingBlock
      title="Download image beside origin image"
      input={
        <Switch defaultChecked>
          <SwitchThumb />
        </Switch>
      }
    />
  )
}

export default SavePathSettingBlock
