import {describe,expect,it} from 'vitest'
import {cityFromComponents,MIN_QUERY,nextOption,shouldSearch} from './places'

describe('address search helpers',()=>{
  it('prefers the locality, then postal town, then district for the city',()=>{
    expect(cityFromComponents([{longText:'Okhla',types:['sublocality']},{longText:'New Delhi',types:['locality','political']}])).toBe('New Delhi')
    expect(cityFromComponents([{longText:'Gurugram',types:['administrative_area_level_3']}])).toBe('Gurugram')
    expect(cityFromComponents([{longText:'Gautam Buddha Nagar',types:['administrative_area_level_2']}])).toBe('Gautam Buddha Nagar')
    expect(cityFromComponents(undefined)).toBe('')
  })
  it('only searches Google after a few meaningful characters',()=>{
    expect(MIN_QUERY).toBe(3)
    expect(shouldSearch('  De ')).toBe(false)
    expect(shouldSearch('Del')).toBe(true)
  })
  it('moves through suggestions with the keyboard and wraps around',()=>{
    expect(nextOption(-1,3,'ArrowDown')).toBe(0)
    expect(nextOption(2,3,'ArrowDown')).toBe(0)
    expect(nextOption(0,3,'ArrowUp')).toBe(2)
    expect(nextOption(1,3,'Home')).toBe(0)
    expect(nextOption(0,3,'End')).toBe(2)
    expect(nextOption(1,0,'ArrowDown')).toBe(-1)
  })
})
